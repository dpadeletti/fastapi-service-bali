from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """
    Endpoint di monitoraggio/salute (Health Check).
    Utilizzato da orchestratori o load balancer per verificare che il servizio 
    sia attivo e raggiungibile.
    """
    return {"status": "ok"}
