import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class UserService {
    private final UserDao dao = new UserDao();

    // VULN-11: 硬编码密钥 + 弱分组模式（ECB）
    private static final byte[] KEY = "0123456789abcdef".getBytes(StandardCharsets.UTF_8); // 16 bytes

    // VULN-12: 不安全随机数用于令牌
    private final Random rng = new Random();

    public String login(String user, String pass, boolean isAdminFromClient) {
        try {
            if (!dao.validateUser(user, pass)) { // VULN-3: DAO 中 SQL 注入导致认证可绕过
                return null;
            }
            String role = isAdminFromClient ? "admin" : "user"; // VULN-10（跨文件）：信任客户端标志导致权限提升
            String tokenPayload = "u=" + user + ";role=" + role + ";nonce=" + rng.nextInt(); // VULN-12
            return encrypt(tokenPayload); // VULN-11
        } catch (Exception e) {
            return null; //（为简单起见吞异常；现实中请记录安全日志）
        }
    }

    public List<String> searchUsers(String q) {
        // VULN-4: DAO 中对 q 拼接 SQL，触发 SQL 注入
        return dao.findUsers(q);
    }

    public String readUserFile(String filename) {
        // VULN-6: 路径遍历（未做白名单/标准化）
        File f = new File("uploads" + File.separator + filename);
        try (FileInputStream fis = new FileInputStream(f)) {
            return new String(fis.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            return "ERR: " + e.getMessage(); // VULN-14: 向客户端泄露内部错误信息
        }
    }

    public String pingHost(String host) {
        // VULN-7: 命令注入（直接拼接到系统命令）
        String[] cmd = {"sh", "-c", "ping -c 1 " + host};
        try {
            Process p = Runtime.getRuntime().exec(cmd);
            p.waitFor();
            try (InputStream is = p.getInputStream()) {
                return new String(is.readAllBytes(), StandardCharsets.UTF_8);
            }
        } catch (Exception e) {
            return "ERR: " + e.getMessage(); // VULN-14
        }
    }

    public String renderProfile(String bio) {
        // VULN-8: 反射型 XSS（未做任何输出编码）
        return "<!doctype html><meta charset='utf-8'><h1>Profile</h1><p>Bio: " + bio + "</p>";
    }

    public String deserializeToken(byte[] data) {
        // VULN-9: 不安全反序列化（对不可信数据直接反序列化）
        try (ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(data))) {
            Object obj = ois.readObject();
            return "Deserialized: " + obj.toString();
        } catch (Exception e) {
            return "ERR: " + e.getMessage(); // VULN-14
        }
    }

    private String encrypt(String s) throws Exception {
        // VULN-11: AES/ECB/PKCS5Padding 易被模式分析；且使用硬编码密钥
        Cipher c = Cipher.getInstance("AES/ECB/PKCS5Padding");
        c.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(KEY, "AES"));
        return Base64.getEncoder().encodeToString(c.doFinal(s.getBytes(StandardCharsets.UTF_8)));
    }
}
