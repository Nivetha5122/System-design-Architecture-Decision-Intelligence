package com.vit.archds.service;

import com.vit.archds.dto.ProjectDtos.DecisionRequest;
import com.vit.archds.entity.*;
import com.vit.archds.repository.*;
import com.vit.archds.security.CurrentUserProvider;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.*;

@Service
public class DecisionService {
 private final ProjectService projects; private final ArchitectureCandidateRepository candidates; private final DecisionRepository decisions; private final AuditLogRepository audit; private final CurrentUserProvider current;
 public DecisionService(ProjectService p,ArchitectureCandidateRepository c,DecisionRepository d,AuditLogRepository a,CurrentUserProvider u){projects=p;candidates=c;decisions=d;audit=a;current=u;}
 @Transactional public Map<String,Object> record(long projectId, DecisionRequest r){
   Project p=projects.get(projectId);
   String key=r==null||r.candidateId()==null?"":r.candidateId().trim();
   ArchitectureCandidate c=null;
   if(!key.isBlank()){
     c=candidates.findByCandidateKey(key).orElse(null);
     if(c==null){try{c=candidates.findById(Long.valueOf(key)).orElse(null);}catch(NumberFormatException ignored){}}
   }
   if(c==null) throw new IllegalArgumentException(key.isBlank()?"No architecture candidate was supplied. Refresh the Decision page and select a candidate again.":"Candidate not found: "+key);
   if(c.getJob().getProject().getId().longValue()!=p.getId()) throw new IllegalArgumentException("Candidate does not belong to this project");
   decisions.save(new Decision(p,c,r==null?null:r.rationale()));
   audit.save(new AuditLog(current.require(),"DECISION_RECORDED","PROJECT",String.valueOf(projectId)));
   return Map.of("message","Decision recorded","candidate_id",c.getId(),"candidate_key",c.getCandidateKey(),"architecture",c.getName());
 }
}
