# dup-pipeline-example

## Step by step simple setup guide

For an architecture overview see [architecture.md](architecture.md)

and see how it relates to the [data-node](dataportal-data-node-architecture.png) setup.


### Setup the dup pipeline components

1. start all components by executing `bash start-all.sh`
2. Download the mii testdata using `bash get-mii-testdata.sh`
3. Upload the mii testdata to your fhir server `bash upload-testdata.sh`
4. Download and Install aether using `bash download-and-install-aether.sh`
5. Download the flatteningLookup `bash get_flattening_lookup.sh`

### Setup the project namespaces an execute

6. Create the necessary DIMP namespaces in the vfps pseuondmyisation service using `bash example-dup-project/example-project-create-namespaces-vfps.sh`
7. Go to the example dup project folder and execute aether `cd example-dup-project && bash example-project-aether-exec.sh`

### Check the project files and get csv output folder

8. When aether finishes it prints a job id on console, which corresponds to a folder for this project in the `example-dup-project/jobs` folder.
9. Inspect the folder - note how it created a csv folder - copy the path to the folder print it by `cd example-dup-project/jobs/<job-id>/csv && pwd`


### Execute a join across the tables to demonstrate simple analysis preparation

10. go to the example-analysis folder `cd example-analysis`
11. Execute the `example_joins.py` with your path from `8.` - e.g. `python3 example_joins.py <path from 8. here>`
12. Inspect the output in joins_output to see what data looks like after some basic joins.


