package vn.edu.atbm.mssv1150080127.crypto;

import java.nio.file.*;
import java.security.*;
import java.security.cert.*;
import java.util.*;

/** Explicit local trust: public certificates are provisioned out of band, never from packages. */
public final class LocalIdentity {
    public static Path directory(){return Path.of(System.getProperty("demo.keys", ".local-keys"));}
    public static char[] password(){
        String value=System.getenv("DEMO_KEYSTORE_PASSWORD");
        if(value==null || value.isEmpty()) throw new IllegalStateException("Set DEMO_KEYSTORE_PASSWORD using scripts/demo.py");
        return value.toCharArray();
    }
    public static KeyStore store(String name) throws Exception {
        char[] pass=password();
        try(var in=Files.newInputStream(directory().resolve(name+".p12"))){
            KeyStore ks=KeyStore.getInstance("PKCS12");ks.load(in,pass);return ks;
        } finally {Arrays.fill(pass,'\0');}
    }
    public static PrivateKey privateKey(String name) throws Exception {
        char[] pass=password();try{return (PrivateKey)store(name).getKey(name,pass);}finally{Arrays.fill(pass,'\0');}
    }
    public static PublicKey publicKey(String name) throws Exception {
        try(var in=Files.newInputStream(directory().resolve(name+".cer"))){
            PublicKey key=CertificateFactory.getInstance("X.509").generateCertificate(in).getPublicKey();
            if(!(key instanceof java.security.interfaces.RSAKey rsa) || rsa.getModulus().bitLength()!=2048)
                throw new InvalidKeyException("RSA-2048 public key required");
            return key;
        }
    }
    public static String fingerprint(PublicKey key) throws Exception {
        return HexFormat.ofDelimiter(":").withUpperCase().formatHex(MessageDigest.getInstance("SHA-256").digest(key.getEncoded()));
    }
    public static void checkPair(String name, PrivateKey key, PublicKey pub) throws Exception {
        if(!((java.security.interfaces.RSAKey)key).getModulus().equals(((java.security.interfaces.RSAKey)pub).getModulus()))
            throw new InvalidKeyException(name+" private key does not match provisioned certificate");
    }
}
