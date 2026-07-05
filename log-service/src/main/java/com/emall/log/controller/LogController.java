package com.emall.log.controller;

import com.emall.log.dto.ResponseResult;
import com.emall.log.exception.BusinessException;
import com.emall.log.service.LogService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.servlet.http.HttpServletResponse;
import java.io.File;
import java.io.IOException;
import java.io.OutputStream;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/log")
public class LogController {

    @Autowired
    private LogService logService;

    @GetMapping("/services")
    public ResponseResult<List<String>> services(
            @RequestHeader(value = "X-User-Role", required = false) String role) {
        requireAdmin(role);
        return ResponseResult.success(logService.listServices());
    }

    @GetMapping("/files")
    public ResponseResult<Map<String, Object>> listFiles(
            @RequestHeader(value = "X-User-Role", required = false) String role) {
        requireAdmin(role);
        return ResponseResult.success(logService.listLogFiles());
    }

    @GetMapping("/tail")
    public ResponseResult<Map<String, Object>> tail(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @RequestParam String file,
            @RequestParam(defaultValue = "200") int lines) {
        requireAdmin(role);
        return ResponseResult.success(logService.tail(file, lines));
    }

    @GetMapping("/search")
    public ResponseResult<Map<String, Object>> search(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @RequestParam String file,
            @RequestParam String keyword,
            @RequestParam(defaultValue = "2") Integer context,
            @RequestParam(defaultValue = "200") Integer max) {
        requireAdmin(role);
        return ResponseResult.success(logService.search(file, keyword, context, max));
    }

    @GetMapping("/download")
    public void download(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @RequestParam String file,
            HttpServletResponse response) throws IOException {
        requireAdmin(role);
        File f = logService.resolveFile(file);
        if (!f.exists() || !f.isFile()) {
            throw new BusinessException(404, "Log file not found: " + file);
        }
        response.setContentType("text/plain; charset=UTF-8");
        response.setContentLengthLong(f.length());
        String fileName = URLEncoder.encode(f.getName(), StandardCharsets.UTF_8.name()).replace("+", "%20");
        response.setHeader(HttpHeaders.CONTENT_DISPOSITION,
                "attachment; filename=\"" + fileName + "\"");
        try (OutputStream os = response.getOutputStream()) {
            Files.copy(f.toPath(), os);
        }
    }

    private void requireAdmin(String role) {
        if (!"ADMIN".equals(role)) {
            throw new BusinessException(403, "Admin role required");
        }
    }
}
