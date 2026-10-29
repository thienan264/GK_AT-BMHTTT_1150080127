package vn.edu.atbm.mssv1150080127.web.service;

import vn.edu.atbm.mssv1150080127.crypto.*;
import vn.edu.atbm.mssv1150080127.util.ReferenceChecks;
import java.security.*;
import java.util.*;

/** Trusted local process. Combined role is a simulation, not multi-user authorization. */
public final class CryptoWebService {
    private static final CryptoWebService INSTANCE=new CryptoWebService();
    private final Map<String,CachedFile> files=new LinkedHashMap<>();
    private PrivateKey alicePrivate,bobPrivate;
    private PublicKey alicePublic,bobPublic;
    private String role;
    private static final long TTL=5*60*1000L;
    private static final long CACHE_LIMIT=64L*1024*1024;
    public record CachedFile(String filename, byte[] data, long expires) {}
    private CryptoWebService(){}
    public static CryptoWebService getInstance(){return INSTANCE;}
    public synchronized void initialize() throws Exception {
        if(role!=null)return;
        String selected=System.getProperty("demo.role","combined");
        if(!Set.of("combined","sender","receiver").contains(selected))throw new IllegalArgumentException("Invalid demo.role");
        PublicKey a=LocalIdentity.publicKey("alice"),b=LocalIdentity.publicKey("bob");
        PrivateKey ap=null,bp=null;
        if(!selected.equals("receiver")){ap=LocalIdentity.privateKey("alice");LocalIdentity.checkPair("alice",ap,a);}
        if(!selected.equals("sender")){bp=LocalIdentity.privateKey("bob");LocalIdentity.checkPair("bob",bp,b);}
        alicePublic=a;bobPublic=b;alicePrivate=ap;bobPrivate=bp;role=selected;
    }
    public Map<String,Object> status() throws Exception {
        initialize();return Map.of("success",true,"mode","Local demo; persistent keys; signed v2; loopback HTTP", "role",role,
            "aliceFingerprint",LocalIdentity.fingerprint(alicePublic),"bobFingerprint",LocalIdentity.fingerprint(bobPublic),
            "signature","RSA-PSS SHA-256, MGF1-SHA-256, salt32", "cacheTtlSeconds",300);
    }
    private synchronized void purge(){
        var it=files.values().iterator();long now=System.currentTimeMillis();
        while(it.hasNext()){var f=it.next();if(f.expires()<=now){Arrays.fill(f.data(),(byte)0);it.remove();}}
    }
    public synchronized CachedFile getCachedFile(String id){purge();var f=files.get(id);return f==null?null:new CachedFile(f.filename(),f.data().clone(),f.expires());}
    public synchronized void clearCache(){for(var f:files.values())Arrays.fill(f.data(),(byte)0);files.clear();}
    private synchronized String cache(String name,byte[] bytes){
        purge();long total=files.values().stream().mapToLong(f->f.data().length).sum();
        if(bytes.length>CACHE_LIMIT)throw new IllegalArgumentException("Artifact exceeds cache limit");
        while(!files.isEmpty() && (files.size()>=20 || total+bytes.length>CACHE_LIMIT)){
            String first=files.keySet().iterator().next();var f=files.remove(first);total-=f.data().length;Arrays.fill(f.data(),(byte)0);
        }
        String id=UUID.randomUUID().toString();files.put(id,new CachedFile(name,bytes,System.currentTimeMillis()+TTL));return id;
    }
    public Map<String,Object> encryptFile(byte[] data,String name,boolean gzip) throws Exception {
        initialize();if(alicePrivate==null)throw new SecurityException("Receiver cannot sign as Alice");
        long start=System.nanoTime();byte[] inner=SecurePackageEngine.pack(data,name,bobPublic,gzip);
        byte[] pkg=SignedPackage.sign(inner,alicePrivate);double ms=(System.nanoTime()-start)/1e6;
        String id=cache(name+".signed.secpkg",pkg);
        return Map.of("success",true,"fileId",id,"originalSize",data.length,"packageSize",pkg.length,"elapsedMs",ms,
            "signature","Alice RSA-PSS", "downloadUrl","/api/download?id="+id);
    }
    public Map<String,Object> decryptFile(byte[] pkg) throws Exception {
        initialize();if(bobPrivate==null)throw new SecurityException("Sender has no Bob private key");
        long start=System.nanoTime();byte[] inner=SignedPackage.verify(pkg,alicePublic);
        var result=SecurePackageEngine.unpack(inner,bobPrivate);double ms=(System.nanoTime()-start)/1e6;
        String id=cache(result.getOriginalFilename(),result.getPlainData());
        return Map.of("success",true,"originalFilename",result.getOriginalFilename(),"originalSize",result.getPlainData().length,
            "elapsedMs",ms,"senderVerified",true,"senderFingerprint",LocalIdentity.fingerprint(alicePublic),
            "notice","Signature does not guarantee malware-free content", "downloadUrl","/api/download?id="+id);
    }
    public Map<String,Object> decryptUnauthorized(byte[] pkg) throws Exception {
        initialize();byte[] inner=SignedPackage.verify(pkg,alicePublic);
        var other=RsaKeyManager.generateKeyPair(2048);
        try {SecurePackageEngine.unpack(inner,other.getPrivate());return Map.of("success",false,"error","Unexpected acceptance");}
        catch(Exception e){return Map.of("success",true,"rejected",true,"reason",e.getClass().getSimpleName());}
    }
    public Map<String,Object> runNistValidation(){try{return ReferenceChecks.run();}catch(Exception e){throw new IllegalStateException("Cannot load reference data",e);}}
}
