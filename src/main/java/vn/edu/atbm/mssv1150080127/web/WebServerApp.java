package vn.edu.atbm.mssv1150080127.web;

import com.sun.net.httpserver.*;
import vn.edu.atbm.mssv1150080127.web.controller.CryptoApiController;
import vn.edu.atbm.mssv1150080127.web.service.CryptoWebService;
import java.net.InetSocketAddress;
import java.util.concurrent.*;

/** Local loopback application for a trusted operator. */
public final class WebServerApp {
    public static void main(String[] args) throws Exception {
        int port=args.length==0?8080:Integer.parseInt(args[0]);
        var service=CryptoWebService.getInstance();service.initialize();
        HttpServer server=HttpServer.create(new InetSocketAddress("127.0.0.1",port),0);
        ExecutorService executor=Executors.newVirtualThreadPerTaskExecutor();server.setExecutor(executor);
        ScheduledExecutorService cleaner=Executors.newSingleThreadScheduledExecutor();

        cleaner.scheduleAtFixedRate(()->service.getCachedFile(""),30,30,TimeUnit.SECONDS);
        server.createContext("/api",new CryptoApiController());
        server.createContext("/",ex->{
            try {
                ex.getResponseHeaders().set("Cache-Control","no-store");
                ex.getResponseHeaders().set("X-Content-Type-Options","nosniff");
                ex.getResponseHeaders().set("X-Frame-Options","DENY");
                if(!ex.getRequestMethod().equals("GET")){ex.sendResponseHeaders(405,-1);return;}
                if(!ex.getRequestURI().getPath().equals("/")){ex.sendResponseHeaders(404,-1);return;}
                try(var input=WebServerApp.class.getResourceAsStream("/static/index.html")){
                    if(input==null){ex.sendResponseHeaders(500,-1);return;}
                    byte[] bytes=input.readAllBytes();ex.getResponseHeaders().set("Content-Type","text/html; charset=utf-8");
                    ex.sendResponseHeaders(200,bytes.length);ex.getResponseBody().write(bytes);
                }
            }finally{ex.close();}
        });
        Runtime.getRuntime().addShutdownHook(new Thread(()->{server.stop(0);cleaner.shutdownNow();executor.shutdownNow();service.clearCache();}));
        server.start();System.out.println("Demo: http://127.0.0.1:"+port+" — "+service.status().get("role"));
        new CountDownLatch(1).await();
    }
}
