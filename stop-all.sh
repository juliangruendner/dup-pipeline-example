COMPOSE_PROJECT=${DSE_EXAMPLE_COMPOSE_PROJECT:-dup-pipeline-example}
BASE_DIR="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 || exit 1 ; pwd -P )"

COMPOSE_IGNORE_ORPHANS=True docker compose -p "$COMPOSE_PROJECT" -f "$BASE_DIR"/vfps/docker-compose.yml stop
COMPOSE_IGNORE_ORPHANS=True docker compose -p "$COMPOSE_PROJECT" -f "$BASE_DIR"/fhir-pseudonymizer/docker-compose.yml stop
COMPOSE_IGNORE_ORPHANS=True docker compose -p "$COMPOSE_PROJECT" -f "$BASE_DIR"/fhir-server/docker-compose.yml stop
COMPOSE_IGNORE_ORPHANS=True docker compose -p "$COMPOSE_PROJECT" -f "$BASE_DIR"/torch/docker-compose.yml stop
COMPOSE_IGNORE_ORPHANS=True docker compose -p "$COMPOSE_PROJECT" -f "$BASE_DIR"/fhir-flattener/docker-compose.yml stop
