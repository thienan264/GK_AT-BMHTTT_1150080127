package vn.edu.atbm.mssv1150080127.experiment;

import vn.edu.atbm.mssv1150080127.crypto.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.io.*;
import java.time.Instant;

/** Reproducible input, fresh cryptographic randomness; timings are wall-clock, not CPU time. */
public class MidtermBenchmark {
    public static void main(String[] args) throws Exception {
        Path output = Path.of(args.length == 0 ? "artifacts/midterm" : args[0]);
        Files.createDirectories(output);
        var keys = RsaKeyManager.generateKeyPair(2048);

        byte[] warm = new byte[100 * 1024]; new Random(42).nextBytes(warm);
        for (int i = 0; i < 5; i++) for (boolean gzip : new boolean[]{false, true}) {
            var pkg = SecurePackageEngine.pack(warm, "benchmark.bin", keys.getPublic(), gzip);
            if (!Arrays.equals(warm, SecurePackageEngine.unpack(pkg, keys.getPrivate()).getPlainData()))
                throw new SecurityException("Warm-up correctness failed");
        }
        Properties config = new Properties();
        config.setProperty("timestamp_utc", Instant.now().toString());
        config.setProperty("seed", "42 (input generation only; keys and nonces use SecureRandom)");
        config.setProperty("runs", "3"); config.setProperty("warmup", "5 per mode, 100 KiB, excluded");
        config.setProperty("order", "alternating baseline/gzip within each repetition");
        config.setProperty("java", System.getProperty("java.runtime.version"));
        config.setProperty("vm", System.getProperty("java.vm.name"));
        config.setProperty("os", System.getProperty("os.name") + " " + System.getProperty("os.version") + " " + System.getProperty("os.arch"));
        config.setProperty("available_processors", "" + Runtime.getRuntime().availableProcessors());
        config.setProperty("max_heap_bytes", "" + Runtime.getRuntime().maxMemory());
        config.setProperty("aes_provider", javax.crypto.Cipher.getInstance("AES/GCM/NoPadding").getProvider().toString());
        config.setProperty("timing_scope", "pack/unpack incl AES key/IV generation, OAEP and GZIP; excludes RSA keypair generation, file/network IO, correctness comparison");
        config.setProperty("resources", "Memory/CPU usage not sampled; available processors and max heap are configuration, not consumption.");
        try (var out = Files.newOutputStream(output.resolve("config.properties"))) { config.store(out, "Midterm experiment configuration"); }
        try (PrintWriter csv = new PrintWriter(Files.newBufferedWriter(output.resolve("raw.csv")))) {
            csv.println("Dataset,Size_Bytes,Mode,RunNumber,EncTime_ms,DecTime_ms,PackageSize_Bytes,Overhead_Bytes,Correct,Input_SHA256");
            for (String dataset : List.of("letters", "random-bytes", "repeated-text")) {
                for (int size : new int[]{1024, 102400, 1048576, 10485760}) {
                    byte[] data = new byte[size]; Random random = new Random(42);
                    if (dataset.equals("random-bytes")) random.nextBytes(data);
                    else for (int i = 0; i < size; i++) data[i] = dataset.equals("letters")
                            ? (byte)('A' + random.nextInt(26)) : (byte)("public synthetic log line 0123456789\n".charAt(i % "public synthetic log line 0123456789\n".length()));
                    String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data));
                    for (int run = 1; run <= 3; run++) {
                        for (int index = 0; index < 2; index++) {
                            boolean gzip = (run % 2 == 1) ? index == 1 : index == 0;
                            long start = System.nanoTime();
                            byte[] pkg = SecurePackageEngine.pack(data, "benchmark.bin", keys.getPublic(), gzip);
                            long middle = System.nanoTime();
                            byte[] plain = SecurePackageEngine.unpack(pkg, keys.getPrivate()).getPlainData();
                            long end = System.nanoTime();
                            boolean correct = Arrays.equals(data, plain);
                            csv.printf(Locale.ROOT, "%s,%d,%s,%d,%.6f,%.6f,%d,%d,%s,%s%n", dataset, size,
                                    gzip ? "Variant_GZIP" : "Baseline", run, (middle-start)/1e6, (end-middle)/1e6,
                                    pkg.length, pkg.length-size, correct, sha);
                            if (!correct) throw new SecurityException("Incorrect benchmark recovery");
                        }
                    }
                }
            }
        }
        System.out.println("Saved benchmark: " + output.toAbsolutePath());
    }
}
