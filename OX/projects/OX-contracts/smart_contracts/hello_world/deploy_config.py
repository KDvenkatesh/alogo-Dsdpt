import logging

import algokit_utils

logger = logging.getLogger(__name__)


# define deployment behaviour based on supplied app spec
def deploy() -> None:
    algorand = algokit_utils.AlgorandClient.from_environment()
    deployer_ = algorand.account.from_environment("DEPLOYER")

    from smart_contracts.artifacts.hello_world.game_fi_d_app_client import (
        GameFiDAppFactory,
        CreateArgs,
    )

    factory = algorand.client.get_typed_app_factory(
        GameFiDAppFactory, default_sender=deployer_.address
    )

    app_client, result = factory.deploy(
        on_update=algokit_utils.OnUpdate.AppendApp,
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
    )

    if result.operation_performed in [
        algokit_utils.OperationPerformed.Create,
        algokit_utils.OperationPerformed.Replace,
    ]:
        algorand.send.payment(
            algokit_utils.PaymentParams(
                amount=algokit_utils.AlgoAmount(algo=1),
                sender=deployer_.address,
                receiver=app_client.app_address,
            )
        )

    # Optional: run a lightweight ABI method to sanity-check the deployed app.
    # `validate_security` is a no-arg method in this contract and safe to call.
    try:
        # Ensure the ABI create initializer runs to populate globals
        app_client.send.create(args=CreateArgs(sender=deployer_.address))
        logger.info(f"Called create initializer on {app_client.app_name} ({app_client.app_id})")

        # Now run a lightweight sanity check
        app_client.send.validate_security()
        logger.info(
            f"Called validate_security on {app_client.app_name} ({app_client.app_id})"
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.warning(f"validate_security call failed: {exc}")
