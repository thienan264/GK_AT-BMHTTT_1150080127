package vn.edu.atbm.mssv1150080127.crypto;

import java.nio.ByteBuffer;
import java.security.*;
import java.security.spec.*;
import java.nio.charset.StandardCharsets;

/** Signed envelope v2 around the unchanged v1 hybrid package. No embedded trust key. */
public final class SignedPackage {
    private static final byte[] MAGIC = {'S','S','P','2'};
    private static final byte[] DOMAIN = "ATBM-SIGNED-PACKAGE-V2".getBytes(StandardCharsets.US_ASCII);
    private static Signature signature() throws Exception {
        Signature s = Signature.getInstance("RSASSA-PSS");
        s.setParameter(new PSSParameterSpec("SHA-256", "MGF1", MGF1ParameterSpec.SHA256, 32, 1));
        return s;
    }
    public static byte[] sign(byte[] inner, PrivateKey alice) throws Exception {
        if (!(alice instanceof java.security.interfaces.RSAKey rsa) || rsa.getModulus().bitLength()!=2048)
            throw new InvalidKeyException("Envelope v2 requires RSA-2048 signing key");
        byte[] content = ByteBuffer.allocate(8+inner.length).put(MAGIC).putInt(inner.length).put(inner).array();
        Signature s=signature(); s.initSign(alice); s.update(DOMAIN); s.update(content);
        byte[] sig=s.sign();
        return ByteBuffer.allocate(content.length+sig.length).put(content).put(sig).array();
    }
    public static byte[] verify(byte[] envelope, PublicKey trustedAlice) throws Exception {
        if (envelope==null || envelope.length<264) throw new SignatureException("Missing signed envelope");
        ByteBuffer b=ByteBuffer.wrap(envelope);
        byte[] magic=new byte[4]; b.get(magic);
        if (!java.util.Arrays.equals(MAGIC,magic)) throw new SignatureException("Signed v2 required; unsigned legacy package rejected");
        int length=b.getInt();
        if(length<0 || length!=envelope.length-264) throw new SignatureException("Invalid envelope length");
        Signature s=signature(); s.initVerify(trustedAlice); s.update(DOMAIN); s.update(envelope,0,8+length);
        if(!s.verify(envelope,8+length,256)) throw new SignatureException("Sender signature rejected");
        return java.util.Arrays.copyOfRange(envelope,8,8+length);
    }
}
