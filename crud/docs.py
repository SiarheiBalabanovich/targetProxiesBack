from sqlalchemy.ext.asyncio import AsyncSession

from models.docs import Param, EndpointParams, Endpoint
from sqlalchemy import select, or_, func, cast, JSON


async def get_api_integration_docs(db: AsyncSession):
    query = (
        select(
            Endpoint.id.label("endpoint_id"),
            Endpoint.name,
            Endpoint.api_endpoint,
            Endpoint.successful_call,
            func.array_agg(
                func.json_build_object(
                    "id", Param.id,
                    "name", Param.name,
                    "type", Param.type,
                    "description", Param.description
                )
            ).label("params")
        )
        .outerjoin(Endpoint.params)
        .outerjoin(EndpointParams.param)
        .group_by(Endpoint.id)
    )

    result = await db.execute(query)

    return result.all()
