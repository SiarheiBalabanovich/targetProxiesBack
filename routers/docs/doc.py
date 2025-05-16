import datetime

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Annotated

from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_session
from crud.base import CRUDService
from crud.docs import get_api_integration_docs

from logic.authorization.validator import AdminVerifier, TokenVerifier

from scheme.docs import ParamScheme, EndpointScheme, ParamCreateScheme, EndpointSchemeCreate, EndpointSchemeResponse

from models.docs import EndpointParams, Param, Endpoint

admin_verifier = AdminVerifier()
verifier = TokenVerifier()

router = APIRouter(responses={
    200: {
        "content": {
            "status": "successful",
        }
    }
})


@router.get('/integration/docs')
async def _get_api_integration_docs(
        offset: int = 0,
        limit: int = 10,
        db: AsyncSession = Depends(get_session)) -> EndpointSchemeResponse:
    result = []
    data = await get_api_integration_docs(db)

    if not len(data):
        raise HTTPException(status_code=404, detail="Docs not found")

    for endpoint_id, endpoint_name, api_endpoint, call, params in data[offset: offset + limit]:
        params = [ParamScheme(**param) for param in params]
        result.append(
            EndpointScheme(
                id=endpoint_id,
                name=endpoint_name,
                api_endpoint=api_endpoint,
                successful_call=call,
                params=params[:]
            )
        )
    return EndpointSchemeResponse(
        total=len(data),
        endpoints=result
    )


@router.post('/integrations/docs/addParam', dependencies=[Depends(admin_verifier)])
async def create_endpoint_param(endpoint_id: int,
                                param: Annotated[ParamCreateScheme, Depends()],
                                db: AsyncSession = Depends(get_session)):
    crud = CRUDService()

    endpoint = await crud.get_by_field(db, Endpoint, 'id', endpoint_id, single=True)
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    param_data = {i: getattr(param, i) for i in param.model_fields_set}
    param_id = await crud.create(db, Param, **param_data)

    await crud.create(db, EndpointParams, **{
        'param_id': param_id,
        'endpoint_id': endpoint_id
    })
    return {
        'status': "successful"
    }


@router.post('/integrations/docs/addEndpoint')
async def create_endpoint(
        endpoint: Annotated[EndpointSchemeCreate, Depends()],
        params: List[ParamCreateScheme],
        db: AsyncSession = Depends(get_session)
):
    crud = CRUDService()

    name, endpoint_, call = endpoint.name, endpoint.api_endpoint, endpoint.successful_call

    params_ids = []

    endpoint_id = await crud.create(db, Endpoint, **{
        'name': name,
        'api_endpoint': endpoint_,
        'successful_call': call
    })

    for param in params:
        data = {i: getattr(param, i) for i in param.model_fields_set}
        param_id = await crud.create(db, Param, **data)

        await crud.create(db, EndpointParams,
                          **{
                            'param_id': param_id,
                            'endpoint_id': endpoint_id
                          })
    return {
        'status': "successful"
    }


@router.patch('/integrations/docs/param/{param_id}', dependencies=[Depends(admin_verifier)])
async def change_param(param_id: int,
                       param: Annotated[ParamCreateScheme, Depends()],
                       db: AsyncSession = Depends(get_session)):
    crud = CRUDService()
    data = {i: getattr(param, i) for i in param.model_fields_set}

    param = await crud.update_fields(db, Param, param_id, **data)
    return {
        "status": "successful"
    }


@router.patch('/integrations/docs/endpoint/{endpoint_id}', dependencies=[Depends(admin_verifier)])
async def update_endpoint(endpoint_id: int,
                          endpoint: Annotated[EndpointSchemeCreate, Depends()],
                          db: AsyncSession = Depends(get_session)):
    crud = CRUDService()

    data = {i: getattr(endpoint, i) for i in endpoint.model_fields_set}
    endpoint = await crud.update_fields(db, Param, endpoint_id, **data)

    return {
        "status": "successful"
    }


@router.delete('/integrations/docs/param/{param_id}', dependencies=[Depends(admin_verifier)])
async def delete_param(param_id: int,
                       db: AsyncSession = Depends(get_session)):
    crud = CRUDService()

    param = await crud.delete(db, Param, param_id)

    return {
        "status": "successful"
    }
