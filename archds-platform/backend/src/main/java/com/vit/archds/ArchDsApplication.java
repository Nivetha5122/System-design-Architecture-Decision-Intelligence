package com.vit.archds;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class ArchDsApplication { public static void main(String[] args){ SpringApplication.run(ArchDsApplication.class,args); } }
