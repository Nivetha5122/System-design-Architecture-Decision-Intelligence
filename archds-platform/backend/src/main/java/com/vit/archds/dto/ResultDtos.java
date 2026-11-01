package com.vit.archds.dto;
import java.util.*;
public final class ResultDtos { private ResultDtos(){}
 public record AnalysisBundle(Map<String,Object> requirementAnalysis,List<Map<String,Object>> candidates,Map<String,Object> optimization,Map<String,Object> verification,List<Map<String,Object>> refinement,List<Map<String,Object>> explanations,Map<String,Object> recommendation,List<Map<String,Object>> traceability,List<Map<String,Object>> history){}
}
