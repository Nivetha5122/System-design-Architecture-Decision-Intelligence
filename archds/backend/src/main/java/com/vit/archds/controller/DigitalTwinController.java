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
@RequestMapping("/api/projects/{projectId}/digital-twin")
public class DigitalTwinController {
    private final ProjectService projects;
    private final AnalysisService analysis;
    private final RestClient ai;
    private final ObjectMapper mapper;

    public DigitalTwinController(ProjectService projects, AnalysisService analysis, RestClient ai, ObjectMapper mapper) {
        this.projects = projects;
        this.analysis = analysis;
        this.ai = ai;
        this.mapper = mapper;
    }

    @GetMapping("/scenarios")
    public JsonNode scenarios(@PathVariable long projectId) {
        Requirement r = projects.latestRequirement(projectId);
        JsonNode result = analysis.result(projectId);
        ObjectNode body = buildRequirements(r);
        body.set("candidate", result.path("recommendation"));
        return ai.post().uri("/api/v1/digital-twin/scenarios").body(body).retrieve().body(JsonNode.class);
    }

    @PostMapping("/simulate")
    public JsonNode simulate(@PathVariable long projectId, @RequestBody Map<String, Object> input) {
        Requirement r = projects.latestRequirement(projectId);
        JsonNode result = analysis.result(projectId);
        ObjectNode body = buildRequirements(r);
        body.set("candidate", result.path("recommendation"));
        body.put("scenario_id", String.valueOf(input.getOrDefault("scenarioId", "traffic_surge")));
        Object intensity = input.getOrDefault("intensity", 1.0);
        if (intensity instanceof Number n) body.put("intensity", n.doubleValue());
        else {
            try { body.put("intensity", Double.parseDouble(String.valueOf(intensity))); }
            catch (Exception e) { body.put("intensity", 1.0); }
        }
        return ai.post().uri("/api/v1/digital-twin/simulate").body(body).retrieve().body(JsonNode.class);
    }

    @PostMapping("/evolve")
    public JsonNode evolve(@PathVariable long projectId, @RequestBody Map<String, Object> input) {
        Requirement r = projects.latestRequirement(projectId);
        JsonNode result = analysis.result(projectId);
        ObjectNode body = buildRequirements(r);
        body.set("candidate", result.path("recommendation"));
        body.put("scenario_id", String.valueOf(input.getOrDefault("scenarioId", "traffic_surge")));
        Object intensity = input.getOrDefault("intensity", 1.0);
        if (intensity instanceof Number n) body.put("intensity", n.doubleValue());
        else {
            try { body.put("intensity", Double.parseDouble(String.valueOf(intensity))); }
            catch (Exception e) { body.put("intensity", 1.0); }
        }
        return ai.post().uri("/api/v1/digital-twin/evolve").body(body).retrieve().body(JsonNode.class);
    }

    private ObjectNode buildRequirements(Requirement r) {
        ObjectNode b = mapper.createObjectNode();
        b.put("project_name", "Digital Twin");
        b.put("description", "");
        b.set("functional_requirements", mapper.valueToTree(split(r.getFunctionalRequirements())));
        b.set("non_functional_requirements", mapper.valueToTree(split(r.getNonFunctionalRequirements())));
        b.set("constraints", mapper.valueToTree(split(r.getConstraints())));
        b.set("technology_preferences", mapper.valueToTree(split(r.getTechnologyPreferences())));
        if (r.getExpectedUsers() != null) b.put("expected_users", r.getExpectedUsers());
        if (r.getBudget() != null) b.put("budget", r.getBudget());
        try { b.set("quality_weights", mapper.readTree(r.getQualityWeightsJson())); }
        catch (Exception e) { b.set("quality_weights", mapper.createObjectNode()); }
        return b;
    }

    private List<String> split(String s) {
        if (s == null || s.isBlank()) return List.of();
        return Arrays.stream(s.split("\\R|;"))
                .map(String::trim).filter(x -> !x.isBlank()).toList();
    }
}
