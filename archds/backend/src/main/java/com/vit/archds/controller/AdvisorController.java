package com.vit.archds.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.vit.archds.service.AnalysisService;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;

@RestController
@RequestMapping("/api/projects/{projectId}/advisor")
public class AdvisorController {
    private final AnalysisService analysis;
    private final RestClient ai;
    private final ObjectMapper mapper;

    public AdvisorController(AnalysisService analysis, RestClient ai, ObjectMapper mapper) {
        this.analysis = analysis; this.ai = ai; this.mapper = mapper;
    }

    @PostMapping
    public JsonNode ask(@PathVariable long projectId, @RequestBody java.util.Map<String,Object> input) {
        String question=String.valueOf(input.getOrDefault("question", "")).trim();
        ObjectNode body=mapper.createObjectNode(); body.put("question", question); body.set("result", analysis.result(projectId));
        return ai.post().uri("/api/v1/advisor").contentType(org.springframework.http.MediaType.APPLICATION_JSON).accept(org.springframework.http.MediaType.APPLICATION_JSON).body(body).retrieve().body(JsonNode.class);
    }
}
