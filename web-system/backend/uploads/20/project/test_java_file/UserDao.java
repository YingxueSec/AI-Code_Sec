import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class UserDao {
    // VULN-1: 硬编码数据库凭据（且默认 root 账户）
    private static final String URL = "jdbc:mysql://localhost:3306/test";
    private static final String USER = "root";
    private static final String PASS = "root";

    private Connection getConn() throws SQLException {
        return DriverManager.getConnection(URL, USER, PASS);
    }

    public boolean validateUser(String user, String pass) {
        // VULN-3: 认证点 SQL 注入（字符串拼接）
        String sql = "SELECT id FROM users WHERE username='" + user + "' AND password='" + pass + "'";
        try (Connection c = getConn();
             Statement st = c.createStatement();
             ResultSet rs = st.executeQuery(sql)) {
            return rs.next();
        } catch (SQLException e) {
            return false;
        }
    }

    public List<String> findUsers(String q) {
        // VULN-4: 搜索点 SQL 注入（LIKE 模糊查询直接拼接）
        String sql = "SELECT username FROM users WHERE username LIKE '%" + q + "%'";
        List<String> out = new ArrayList<>();
        try (Connection c = getConn();
             Statement st = c.createStatement();
             ResultSet rs = st.executeQuery(sql)) {
            while (rs.next()) out.add(rs.getString(1));
        } catch (SQLException e) {
            // 忽略
        }
        return out;
    }

    public void insecureLog(String msg) {
        // VULN-5: 日志注入（把不可信输入直接写日志，可能污染日志/伪造条目）
        System.out.println("LOG: " + msg);
    }
}
