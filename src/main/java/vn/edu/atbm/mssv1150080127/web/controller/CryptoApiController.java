package vn.edu.atbm.mssv1150080127.web.controller;

import com.google.gson.Gson;
import com.sun.net.httpserver.*;
import vn.edu.atbm.mssv1150080127.web.service.CryptoWebService;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public final class CryptoApiController implements HttpHandler {
    private final CryptoWebService service=CryptoWebService.getInstance();
    private final Gson gson=new Gson();
    private static final int MAX_UPLOAD=21*1024*1024;
    public void handle(HttpExchange ex) throws IOException {
        try {
            ex.getResponseHeaders().set("Cache-Control","no-store");
            ex.getResponseHeaders().set("X-Content-Type-Options","nosniff");
            String origin=ex.getRequestHeaders().getFirst("Origin");
            String host=ex.getRequestHeaders().getFirst("Host");
            String fetchSite=ex.getRequestHeaders().getFirst("Sec-Fetch-Site");
            if("cross-site".equals(fetchSite)) {json(ex,403,Map.of("success",false,"error","Cross-site request rejected"));return;}
            if(host==null || !(host.equals("localhost:"+ex.getLocalAddress().getPort()) || host.equals("127.0.0.1:"+ex.getLocalAddress().getPort()))) {
                json(ex,403,Map.of("success",false,"error","Local host required"));return;
            }
            if(origin!=null && !origin.equals("http://"+host)) {json(ex,403,Map.of("success",false,"error","Cross-origin request rejected"));return;}
            String path=ex.getRequestURI().getPath();var q=query(ex.getRequestURI());
            if(path.equals("/api/status")){json(ex,200,service.status());return;}
            if(path.equals("/api/nist")&&ex.getRequestMethod().equals("GET")){json(ex,200,service.runNistValidation());return;}
            if(path.equals("/api/download")&&ex.getRequestMethod().equals("GET")){
                var file=service.getCachedFile(q.getOrDefault("id",""));if(file==null){json(ex,404,Map.of("success",false,"error","Artifact not found; restart/eviction may remove it"));return;}
                String name=URLEncoder.encode(file.filename(),StandardCharsets.UTF_8).replace("+","%20");
                ex.getResponseHeaders().set("Content-Type","application/octet-stream");ex.getResponseHeaders().set("Content-Disposition","attachment; filename*=UTF-8''"+name);

                ex.sendResponseHeaders(200,file.data().length);ex.getResponseBody().write(file.data());return;
            }
            if(!Set.of("/api/encrypt","/api/decrypt","/api/decrypt-unauthorized").contains(path)){json(ex,404,Map.of("success",false,"error","Unknown endpoint"));return;}
            if(!ex.getRequestMethod().equals("POST")){json(ex,405,Map.of("success",false,"error","POST required"));return;}
            if(path.equals("/api/encrypt") && "receiver".equals(System.getProperty("demo.role")))throw new SecurityException("Receiver role");
            byte[] body=ex.getRequestBody().readNBytes(MAX_UPLOAD+1);
            if(body.length>MAX_UPLOAD){json(ex,413,Map.of("success",false,"error","Demo limit: 20 MiB"));return;}
            if(path.equals("/api/encrypt") && body.length>20*1024*1024){json(ex,413,Map.of("success",false,"error","Plaintext limit: 20 MiB"));return;}
            var result=switch(path){
                case "/api/encrypt" -> service.encryptFile(body,q.getOrDefault("filename","document.bin"),Boolean.parseBoolean(q.getOrDefault("gzip","false")));
                case "/api/decrypt" -> service.decryptFile(body);
                default -> service.decryptUnauthorized(body);
            };
            json(ex,200,result);
        } catch(Exception e){json(ex,400,Map.of("success",false,"error","Gói hoặc yêu cầu không hợp lệ; không trả bản rõ.","reason",e.getClass().getSimpleName()));}
        finally{ex.close();}
    }
    private Map<String,String> query(URI uri){Map<String,String> q=new HashMap<>();if(uri.getRawQuery()!=null)for(String pair:uri.getRawQuery().split("&")){String[] p=pair.split("=",2);q.put(URLDecoder.decode(p[0],StandardCharsets.UTF_8),p.length==2?URLDecoder.decode(p[1],StandardCharsets.UTF_8):"");}return q;}
    private void json(HttpExchange ex,int code,Object value)throws IOException{byte[] bytes=gson.toJson(value).getBytes(StandardCharsets.UTF_8);ex.getResponseHeaders().set("Content-Type","application/json; charset=utf-8");ex.getResponseHeaders().set("Cache-Control","no-store");ex.sendResponseHeaders(code,bytes.length);ex.getResponseBody().write(bytes);}
}
