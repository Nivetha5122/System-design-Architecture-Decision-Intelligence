package com.vit.archds.dto;
import com.fasterxml.jackson.annotation.JsonAlias; import jakarta.validation.constraints.*; import java.time.Instant; import java.util.*;
public final class ProjectDtos { private ProjectDtos(){}
 public record CreateProject(@NotBlank @Size(max=160) String name,@Size(max=4000) String description){}
 public record ProjectResponse(Long id,String name,String description,Instant createdAt,Instant updatedAt){}
 public record Requirements(
  @Size(max=12000) @JsonAlias({"functionalRequirements","functional_requirements"}) String functionalRequirements,
  @Size(max=12000) @JsonAlias({"nonFunctionalRequirements","non_functional_requirements"}) String nonFunctionalRequirements,
  @Size(max=8000) @JsonAlias({"constraints"}) String constraints,
  @Size(max=4000) @JsonAlias({"technologyPreferences","technology_preferences"}) String technologyPreferences,
  @JsonAlias({"expectedUsers","expected_users"}) String expectedUsers,
  @Size(max=500) @JsonAlias({"budget"}) String budget,
  @JsonAlias({"qualityWeights","quality_weights"}) Map<String,Integer> qualityWeights,
  @Min(2) @Max(8) @JsonAlias({"alternatives","num_alternatives"}) Integer alternatives,
  @Min(1) @Max(5) @JsonAlias({"maxIterations","max_iterations"}) Integer maxIterations
 ){}
 public record JobResponse(String jobId,String status,int progress,String currentStage,String message,String errorMessage,Instant createdAt,Instant startedAt,Instant completedAt){}
 public record DecisionRequest(@JsonAlias({"candidateId","candidate_id","candidateKey","candidate_key"}) String candidateId,@Size(max=4000) String rationale){}
}
