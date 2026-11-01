package com.vit.archds.controller;

import com.vit.archds.repository.AuditLogRepository;
import com.vit.archds.security.CurrentUserProvider;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/audit")
public class AuditController {
    private final AuditLogRepository repo;
    private final CurrentUserProvider current;

    public AuditController(AuditLogRepository r, CurrentUserProvider c) {
        repo = r;
        current = c;
    }

    @GetMapping
    public List<Map<String, Object>> list() {
        List<Map<String, Object>> result = new ArrayList<>();
        repo.findTop100ByUserOrderByTimestampDesc(current.require()).forEach(a -> {
            Map<String, Object> item = new java.util.LinkedHashMap<>();
            item.put("id", a.getId());
            item.put("action", a.getAction());
            item.put("resource", a.getResource() == null ? "" : a.getResource());
            item.put("metadata", a.getMetadata() == null ? "" : a.getMetadata());
            item.put("timestamp", a.getTimestamp());
            result.add(item);
        });
        return result;
    }
}
