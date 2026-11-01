package com.vit.archds.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.vit.archds.service.AnalysisService;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClientResponseException;

import java.nio.charset.StandardCharsets;

@RestController
@RequestMapping("/api/projects/{projectId}")
public class ReportController {
    private final AnalysisService analysis;
    private final RestClient ai;

    public ReportController(AnalysisService analysis, @org.springframework.beans.factory.annotation.Value("${app.ai-service.base-url:http://localhost:8000}") String aiBaseUrl) {
        this.analysis = analysis;
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(10000);
        factory.setReadTimeout(12000);
        this.ai = RestClient.builder().baseUrl(aiBaseUrl).requestFactory(factory).build();
    }

    @GetMapping(value = "/report.pdf", produces = MediaType.APPLICATION_PDF_VALUE)
    public ResponseEntity<byte[]> pdf(@PathVariable long projectId) {
        JsonNode result = analysis.result(projectId);
        try {
            var response = ai.post()
                    .uri("/api/v1/report/pdf")
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_PDF)
                    .header(HttpHeaders.CACHE_CONTROL, "no-store")
                    .body(result)
                    .retrieve()
                    .toEntity(byte[].class);
            byte[] pdf = response.getBody();
            if (response.getStatusCode().is2xxSuccessful() && isPdf(pdf)) {
                return pdfResponse(pdf, "ARCHDS_Architecture_Report.pdf", "ai");
            }
            System.err.println("[ARCHDS] AI report service returned a non-PDF response; using local fallback report.");
        } catch (RestClientResponseException ex) {
            System.err.println("[ARCHDS] AI PDF service failed: " + ex.getStatusCode() + " " + ex.getResponseBodyAsString());
        } catch (Exception ex) {
            System.err.println("[ARCHDS] AI PDF service unavailable: " + ex.getMessage());
        }
        // Never leave the user with a broken download. The fallback is a valid PDF and preserves the key decision.
        return pdfResponse(fallbackPdf(projectId, result), "ARCHDS_Architecture_Report.pdf", "local-fallback");
    }

    private static boolean isPdf(byte[] b) {
        return b != null && b.length >= 5 && b[0]=='%' && b[1]=='P' && b[2]=='D' && b[3]=='F' && b[4]=='-';
    }

    private static ResponseEntity<byte[]> pdfResponse(byte[] pdf, String name, String source) {
        return ResponseEntity.ok().contentType(MediaType.APPLICATION_PDF)
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=" + name)
                .header(HttpHeaders.CACHE_CONTROL, "no-store, no-cache, must-revalidate")
                .header("X-ARCHDS-Report", source)
                .body(pdf);
    }

    /** Minimal valid PDF fallback used only when the AI report renderer is unavailable. */
    private static byte[] fallbackPdf(long projectId, JsonNode result) {
        String project = text(result, "project_name", "Architecture Study " + projectId);
        JsonNode rec = result.path("recommendation");
        String architecture = text(rec, "name", "No recommendation available");
        String description = text(rec, "description", "The detailed report renderer was unavailable; the core decision is preserved in this fallback report.");
        String content = "BT /F1 18 Tf 50 760 Td (ARCHDS Architecture Decision Report) Tj "
                + "/F1 12 Tf 0 -32 Td (Project: " + esc(project) + ") Tj "
                + "0 -24 Td (Selected architecture: " + esc(architecture) + ") Tj "
                + "0 -24 Td (Project ID: " + projectId + ") Tj "
                + "0 -32 Td (Summary:) Tj 0 -20 Td (" + esc(wrap(description, 95)) + ") Tj ET";
        String[] objects = new String[] {
                "<< /Type /Catalog /Pages 2 0 R >>",
                "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
                "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
                "<< /Length " + content.getBytes(StandardCharsets.ISO_8859_1).length + " >>\nstream\n" + content + "\nendstream"
        };
        StringBuilder pdf = new StringBuilder("%PDF-1.4\n%ARCHDS\n");
        long[] offsets = new long[objects.length + 1];
        for (int i=0;i<objects.length;i++) { offsets[i+1]=pdf.toString().getBytes(StandardCharsets.ISO_8859_1).length; pdf.append(i+1).append(" 0 obj\n").append(objects[i]).append("\nendobj\n"); }
        long xref=pdf.toString().getBytes(StandardCharsets.ISO_8859_1).length;
        pdf.append("xref\n0 ").append(objects.length+1).append("\n0000000000 65535 f \n");
        for(int i=1;i<offsets.length;i++) pdf.append(String.format("%010d 00000 n \n", offsets[i]));
        pdf.append("trailer\n<< /Size ").append(objects.length+1).append(" /Root 1 0 R >>\nstartxref\n").append(xref).append("\n%%EOF\n");
        return pdf.toString().getBytes(StandardCharsets.ISO_8859_1);
    }
    private static String text(JsonNode n, String key, String fallback) { String v=n.path(key).asText("").trim(); return v.isBlank()?fallback:v; }
    private static String esc(String s) { return s.replace("\\","\\\\").replace("(","\\(").replace(")","\\)").replace("\r"," ").replace("\n"," "); }
    private static String wrap(String s,int max){String v=s.replaceAll("\\s+"," ");return v.length()>max?v.substring(0,max-3)+"...":v;}
}
