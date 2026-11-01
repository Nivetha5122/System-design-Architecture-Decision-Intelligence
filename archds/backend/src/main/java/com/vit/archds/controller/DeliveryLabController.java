package com.vit.archds.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.vit.archds.entity.Requirement;
import com.vit.archds.service.AnalysisService;
import com.vit.archds.service.ProjectService;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;
import java.util.*;

@RestController
@RequestMapping("/api/projects/{projectId}/delivery-lab")
public class DeliveryLabController {
    private final ProjectService projects;
    private final AnalysisService analysis;
    private final RestClient ai;
    private final ObjectMapper mapper;

    public DeliveryLabController(ProjectService projects, AnalysisService analysis, RestClient ai, ObjectMapper mapper) {
        this.projects = projects; this.analysis = analysis; this.ai = ai; this.mapper = mapper;
    }

    @PostMapping("/generate")
    public JsonNode generate(@PathVariable long projectId) {
        Requirement r = projects.latestRequirement(projectId);
        JsonNode result = analysis.result(projectId);
        ObjectNode body = mapper.createObjectNode();
        body.put("project_name", "ARCHDS Delivery Lab");
        body.put("description", "");
        body.set("functional_requirements", mapper.valueToTree(split(r.getFunctionalRequirements())));
        body.set("non_functional_requirements", mapper.valueToTree(split(r.getNonFunctionalRequirements())));
        body.set("constraints", mapper.valueToTree(split(r.getConstraints())));
        body.set("technology_preferences", mapper.valueToTree(split(r.getTechnologyPreferences())));
        if (r.getExpectedUsers() != null) body.put("expected_users", r.getExpectedUsers());
        if (r.getBudget() != null) body.put("budget", r.getBudget());
        body.set("candidate", result.path("recommendation"));
        return ai.post().uri("/api/v1/delivery/generate").body(body).retrieve().body(JsonNode.class);
    }

    private List<String> split(String s) {
        if (s == null || s.isBlank()) return List.of();
        return Arrays.stream(s.split("\\R|;" )).map(String::trim).filter(x -> !x.isBlank()).toList();
    }
}
