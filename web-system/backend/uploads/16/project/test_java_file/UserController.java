import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.Headers;

import java.io.IOException;
import java.io.OutputStream;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class UserController {
    private static UserService service = new UserService();

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.createContext("/login", UserController::handleLogin);
        server.createContext("/search", UserController::handleSearch);
        server.createContext("/file", UserController::handleReadFile);
        server.createContext("/exec", UserController::handleExec);
        server.createContext("/profile", UserController::handleProfile);
        server.createContext("/deserialize", UserController::handleDeserialize);
        System.out.println("Demo server started on http://localhost:8080");
        server.start();
    }

    private static void handleLogin(HttpExchange ex) throws IOException {
        Map<String,String> p = parseQuery(ex.getRequestURI().getRawQuery());
        String u = p.getOrDefault("user", "");
        String pw = p.getOrDefault("pass", "");
        boolean isAdminFromClient = "true".equalsIgnoreCase(p.getOrDefault("admin", "false"));
        // VULN-10: 信任来自客户端的 admin 标志（跨文件：Controller→Service）
        String token = service.login(u, pw, isAdminFromClient);
        writeText(ex, token == null ? "Login failed" : "OK token=" + token);
    }

    private static void handleSearch(HttpExchange ex) throws IOException {
        Map<String,String> p = parseQuery(ex.getRequestURI().getRawQuery());
        String q = p.getOrDefault("q", "");
        String out = String.join(",", service.searchUsers(q)); // VULN-4 由 Service/DAO 触发的 SQLi
        writeText(ex, out);
    }

    private static void handleReadFile(HttpExchange ex) throws IOException {
        Map<String,String> p = parseQuery(ex.getRequestURI().getRawQuery());
        String name = p.getOrDefault("name", "");
        String content = service.readUserFile(name); // VULN-6 路径遍历
        writeText(ex, content);
    }

    private static void handleExec(HttpExchange ex) throws IOException {
        Map<String,String> p = parseQuery(ex.getRequestURI().getRawQuery());
        String host = p.getOrDefault("host", "127.0.0.1");
        String output = service.pingHost(host); // VULN-7 命令注入
        writeText(ex, output);
    }

    private static void handleProfile(HttpExchange ex) throws IOException {
        Map<String,String> p = parseQuery(ex.getRequestURI().getRawQuery());
        String bio = p.getOrDefault("bio", "");
        String html = service.renderProfile(bio); // VULN-8 反射型 XSS
        Headers h = ex.getResponseHeaders();
        h.add("Content-Type", "text/html; charset=utf-8");
        writeText(ex, html);
    }

    private static void handleDeserialize(HttpExchange ex) throws IOException {
        byte[] body = ex.getRequestBody().readAllBytes();
        String result = service.deserializeToken(body); // VULN-9 不安全反序列化
        writeText(ex, result);
    }

    private static Map<String,String> parseQuery(String raw) throws IOException {
        Map<String,String> m = new HashMap<>();
        if (raw == null || raw.isEmpty()) return m;
        for (String kv : raw.split("&")) {
            String[] parts = kv.split("=", 2);
            String k = URLDecoder.decode(parts[0], StandardCharsets.UTF_8);
            String v = parts.length > 1 ? URLDecoder.decode(parts[1], StandardCharsets.UTF_8) : "";
            m.put(k, v);
        }
        return m;
    }

    private static void writeText(HttpExchange ex, String s) throws IOException {
        byte[] data = s.getBytes(StandardCharsets.UTF_8);
        ex.sendResponseHeaders(200, data.length);
        try (OutputStream os = ex.getResponseBody()) {
            os.write(data);
        }
    }
}
