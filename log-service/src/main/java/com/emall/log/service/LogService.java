package com.emall.log.service;

import com.emall.log.exception.BusinessException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.io.RandomAccessFile;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class LogService {

    @Value("${emall.log.root:logs}")
    private String logRoot;

    @Value("${emall.log.max-file-size-mb:50}")
    private int maxFileSizeMb;

    @Value("${emall.log.max-tail-lines:5000}")
    private int maxTailLines;

    private static final List<String> ALLOWED_SUFFIXES = Arrays.asList(".log", ".out", ".txt");
    private static final List<String> SERVICE_NAMES = Arrays.asList(
            "user-service", "product-service", "order-service",
            "inventory-service", "gateway", "log-service");

    public Map<String, Object> listLogFiles() {
        File root = resolveRoot();
        List<Map<String, Object>> files = new ArrayList<>();
        if (root.exists() && root.isDirectory()) {
            File[] subs = root.listFiles();
            if (subs != null) {
                for (File f : subs) {
                    if (f.isFile() && isLogFile(f.getName())) {
                        files.add(toFileInfo(f, resolveService(f.getName())));
                    }
                }
                // 也列出子目录 (例如 csp 子目录里的 sentinel 日志)
                for (File sub : subs) {
                    if (sub.isDirectory()) {
                        File[] innerFiles = sub.listFiles();
                        if (innerFiles != null) {
                            for (File f : innerFiles) {
                                if (f.isFile() && isLogFile(f.getName())) {
                                    files.add(toFileInfo(f, resolveService(f.getName()) + "/" + sub.getName()));
                                }
                            }
                        }
                    }
                }
            }
        }
        files.sort(Comparator.comparing((Map<String, Object> m) -> ((Date) m.get("lastModified"))).reversed());
        Map<String, Object> result = new HashMap<>();
        result.put("root", root.getAbsolutePath());
        result.put("total", files.size());
        result.put("files", files);
        return result;
    }

    public Map<String, Object> tail(String file, int lines) {
        if (lines <= 0) lines = 200;
        if (lines > maxTailLines) lines = maxTailLines;
        File f = resolveFile(file);
        if (!f.exists() || !f.isFile()) {
            throw new BusinessException(404, "Log file not found: " + file);
        }
        long sizeBytes = f.length();
        if (sizeBytes > maxFileSizeMb * 1024L * 1024L) {
            throw new BusinessException(413, "Log file too large (> " + maxFileSizeMb + "MB) for tail, use download");
        }

        List<String> content = new ArrayList<>();
        try (RandomAccessFile raf = new RandomAccessFile(f, "r")) {
            long pos = raf.length();
            long cur = pos - 1;
            int count = 0;
            StringBuilder sb = new StringBuilder();
            while (cur >= 0 && count <= lines) {
                raf.seek(cur);
                int c = raf.read();
                if (c == '\n' && cur < pos - 1) {
                    content.add(0, sb.reverse().toString());
                    sb.setLength(0);
                    count++;
                } else if (c != '\r') {
                    sb.append((char) c);
                }
                cur--;
            }
            if (sb.length() > 0) {
                content.add(0, sb.reverse().toString());
            }
        } catch (Exception e) {
            throw new BusinessException(500, "Failed to tail log: " + e.getMessage());
        }

        Map<String, Object> result = new HashMap<>();
        result.put("file", file);
        result.put("size", sizeBytes);
        result.put("lines", content.size());
        result.put("content", content);
        return result;
    }

    public Map<String, Object> search(String file, String keyword, Integer context, Integer maxResults) {
        if (keyword == null || keyword.isEmpty()) {
            throw new BusinessException(400, "keyword is required");
        }
        int ctx = context == null || context < 0 ? 2 : context;
        int limit = maxResults == null || maxResults <= 0 ? 200 : Math.min(maxResults, 2000);
        File f = resolveFile(file);
        if (!f.exists() || !f.isFile()) {
            throw new BusinessException(404, "Log file not found: " + file);
        }

        List<Map<String, Object>> matches = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(
                new InputStreamReader(new FileInputStream(f), StandardCharsets.UTF_8))) {
            String line;
            int lineNo = 0;
            while ((line = br.readLine()) != null) {
                lineNo++;
                if (line.contains(keyword)) {
                    Map<String, Object> m = new HashMap<>();
                    m.put("line", lineNo);
                    m.put("content", line);
                    matches.add(m);
                    if (matches.size() >= limit) break;
                }
            }
        } catch (Exception e) {
            throw new BusinessException(500, "Failed to search log: " + e.getMessage());
        }

        Map<String, Object> result = new HashMap<>();
        result.put("file", file);
        result.put("keyword", keyword);
        result.put("matches", matches.size());
        result.put("context", ctx);
        result.put("hits", matches);
        return result;
    }

    public File resolveFile(String file) {
        if (file == null || file.isEmpty()) {
            throw new BusinessException(400, "file is required");
        }
        File root = resolveRoot();
        File f;
        // 如果是绝对路径且在 root 之下 -> 直接使用
        File abs = new File(file);
        if (abs.isAbsolute()) {
            try {
                String rootCanonical = root.getCanonicalPath();
                String fileCanonical = abs.getCanonicalPath();
                if (!fileCanonical.startsWith(rootCanonical)) {
                    throw new BusinessException(400, "Invalid file path (outside log root)");
                }
                f = abs;
            } catch (BusinessException e) {
                throw e;
            } catch (Exception e) {
                throw new BusinessException(400, "Invalid file path");
            }
        } else {
            // 相对路径: 禁止路径穿越
            if (file.contains("..")) {
                throw new BusinessException(400, "Invalid file path");
            }
            f = new File(root, file);
        }
        // 二次校验: 解析后必须在 root 之下
        try {
            String rootCanonical = root.getCanonicalPath();
            String fileCanonical = f.getCanonicalPath();
            if (!fileCanonical.startsWith(rootCanonical)) {
                throw new BusinessException(400, "Invalid file path (outside log root)");
            }
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            throw new BusinessException(400, "Invalid file path");
        }
        return f;
    }

    public File resolveRoot() {
        File f = new File(logRoot);
        if (!f.isAbsolute()) {
            // 相对路径时，相对 user.dir
            f = new File(System.getProperty("user.dir"), logRoot);
        }
        return f;
    }

    private Map<String, Object> toFileInfo(File f, String service) {
        Map<String, Object> m = new HashMap<>();
        m.put("name", f.getName());
        m.put("path", f.getAbsolutePath());
        m.put("service", service);
        m.put("size", f.length());
        m.put("lastModified", new Date(f.lastModified()));
        return m;
    }

    private boolean isLogFile(String name) {
        String lower = name.toLowerCase();
        return ALLOWED_SUFFIXES.stream().anyMatch(lower::endsWith);
    }

    private String resolveService(String fileName) {
        String lower = fileName.toLowerCase();
        for (String s : SERVICE_NAMES) {
            if (lower.startsWith(s.toLowerCase())) {
                return s;
            }
        }
        return "other";
    }

    public List<String> listServices() {
        return SERVICE_NAMES;
    }
}
