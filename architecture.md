# Architecture

Components started by `start-all.sh` run as Docker containers in one Compose project (`dup-pipeline-example`) and reach each other by service name. Aether, the setup scripts and the analysis script run on the host and reach the containers through the published `localhost` ports.

```mermaid
flowchart LR
    subgraph host["Host"]
        upload["upload-testdata.sh"]
        ns["example-project-create-namespaces-vfps.sh"]
        aether["aether CLI<br/>(example-project-pipeline.yml)"]
        jobs@{ shape: docs, label: "example-dup-project/jobs/{job-id}/csv" }
        joins["example-analysis/example_joins.py"]
        joinsout@{ shape: docs, label: "example-analysis/joins_output" }
    end

    subgraph docker["Docker Compose project: dup-pipeline-example"]
        subgraph fhirsrv["fhir-server/"]
            blaze["fhir-server<br/>Blaze :8088"]
            blazedup["fhir-server-dup<br/>Blaze :8089<br/>(not used by pipeline)"]
        end

        subgraph torchgrp["torch/"]
            torch["torch<br/>:8086"]
            nginx["torch-nginx<br/>:80"]
            torchvol[("triangle-torch-data-store")]
        end

        subgraph pseudo["fhir-pseudonymizer/ + vfps/"]
            dimp["fhir-pseudonymizer (DIMP)<br/>:8083"]
            vfps["vfps<br/>:8090 REST, 8081 gRPC internal"]
            pg[("postgresql<br/>:35432")]
        end

        flattener["fhir-flattener<br/>:8091"]
    end

    upload -- "POST bundles" --> blaze
    ns -- "POST /v1/namespaces" --> vfps

    aether -- "1. CRTDL extraction" --> torch
    torch -- "FHIR search" --> blaze
    torch -- "writes NDJSON" --> torchvol
    torchvol --- nginx
    aether -- "download NDJSON" --> nginx

    aether -- "2. $de-identify" --> dimp
    dimp -- "gRPC pseudonyms" --> vfps
    vfps --> pg

    aether -- "3. flatten to CSV" --> flattener
    aether -- "writes" --> jobs
    jobs --> joins
    joins -- "writes" --> joinsout
```

Pipeline steps enabled in `example-project-pipeline.yml`: `torch`, `dimp`, `flattening`. The `send` and `validation` steps are configured but disabled, so `fhir-server-dup` receives no data.
