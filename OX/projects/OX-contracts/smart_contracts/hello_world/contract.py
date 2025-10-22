"""
Simplified Algopy ARC4Contract for local development and static checks.

Notes:
- Inner transaction and chain-time behavior are represented with conservative
  stubs suitable for static compilation and unit testing. Replace or extend
  with real runtime fields and itxn parameters when integrating with AlgoKit
  LocalNet.
"""

from algopy import (
    ARC4Contract,
    Account,
    UInt64,
    Bytes,
    GlobalState,
    BoxMap,
    gtxn,
    itxn,
    op,
)
from algopy.arc4 import abimethod, UInt64 as ARC4UInt64, Address, Struct


class PlayerState(Struct):
    algo_balance: ARC4UInt64
    mint_balance: ARC4UInt64
    spot_balance: ARC4UInt64
    staked_mint: ARC4UInt64
    staked_spot: ARC4UInt64
    nfts_owned: ARC4UInt64
    last_stake_timestamp: ARC4UInt64


class GameFiDApp(ARC4Contract):
    oracle_address: GlobalState[Address]
    mint_token_asa: GlobalState[UInt64]
    spot_token_asa: GlobalState[UInt64]
    stake_reward_rate: GlobalState[UInt64]
    spot_price_algo: GlobalState[UInt64]
    mint_price_algo: GlobalState[UInt64]
    tinyman_validator_app_id: GlobalState[UInt64]
    mint_algo_pool_app_id: GlobalState[UInt64]
    spot_mint_pool_app_id: GlobalState[UInt64]
    game_fees_treasury_algo: GlobalState[UInt64]
    game_fees_treasury_mint: GlobalState[UInt64]
    game_fees_treasury_spot: GlobalState[UInt64]

    def __init__(self) -> None:
        super().__init__()
        self.player_states = BoxMap(Account, PlayerState)

    def _to_int(self, v: object) -> int:
        try:
            return int(v)
        except Exception:
            return 0

    def _gs_uint(self, gs: GlobalState[UInt64]) -> int:
        val, exists = gs.maybe()
        if not exists:
            return 0
        return self._to_int(val)

    @abimethod
    def app_create(self, oracle_addr: Address, tinyman_validator_id: UInt64, mint_algo_pool_id: UInt64, spot_mint_pool_id: UInt64) -> None:
        self.oracle_address.value = oracle_addr
        # GlobalState expects algopy.UInt64 values
        self.tinyman_validator_app_id.value = UInt64(self._to_int(tinyman_validator_id))
        self.mint_algo_pool_app_id.value = UInt64(self._to_int(mint_algo_pool_id))
        self.spot_mint_pool_app_id.value = UInt64(self._to_int(spot_mint_pool_id))

        self.spot_price_algo.value = UInt64(1000)
        self.mint_price_algo.value = UInt64(10000)
        self.stake_reward_rate.value = UInt64(1)
        self.game_fees_treasury_algo.value = UInt64(0)
        self.game_fees_treasury_mint.value = UInt64(0)
        self.game_fees_treasury_spot.value = UInt64(0)

    @abimethod
    def get_player_state(self, player: Account) -> PlayerState:
        state, exists = self.player_states.maybe(player)
        if not exists:
            return PlayerState(ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0))
        return state

    @abimethod
    def deposit_algo(self, payment: gtxn.PaymentTransaction) -> None:
        # receiver should be the application address (checked off-chain or by group semantics)
        sender = payment.sender
        state, exists = self.player_states.maybe(sender)
        if not exists:
            state = PlayerState(ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0))
        state.algo_balance = ARC4UInt64(self._to_int(state.algo_balance) + self._to_int(payment.amount))
        self.player_states[sender] = state

    @abimethod
    def deposit_asa(self, payment: gtxn.AssetTransferTransaction, token_id: UInt64) -> None:
        # Ensure receiver and asset id are provided by the grouped transaction
        sender = payment.sender
        state, exists = self.player_states.maybe(sender)
        if not exists:
            state = PlayerState(ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0))
        mint_id = self._gs_uint(self.mint_token_asa)
        spot_id = self._gs_uint(self.spot_token_asa)
        if int(token_id) == mint_id:
            state.mint_balance = ARC4UInt64(self._to_int(state.mint_balance) + self._to_int(payment.amount))
        elif int(token_id) == spot_id:
            state.spot_balance = ARC4UInt64(self._to_int(state.spot_balance) + self._to_int(payment.amount))
        else:
            raise Exception("Invalid ASA for deposit")
        self.player_states[sender] = state

    @abimethod
    def withdraw_algo(self, amount: UInt64, sender: Account) -> None:
        state, exists = self.player_states.maybe(sender)
        if not exists or self._to_int(state.algo_balance) < self._to_int(amount):
            raise Exception("insufficient balance")
        state.algo_balance = ARC4UInt64(self._to_int(state.algo_balance) - self._to_int(amount))
        self.player_states[sender] = state
        pay = itxn.Payment(receiver=sender, amount=self._to_int(amount))
        pay.submit()

    @abimethod
    def stake_mint_tokens(self, amount: UInt64, sender: Account) -> None:
        state, exists = self.player_states.maybe(sender)
        if not exists or self._to_int(state.mint_balance) < self._to_int(amount):
            raise Exception("insufficient mint to stake")
        now = 0
        elapsed = max(0, now - self._to_int(state.last_stake_timestamp))
        rate = self._gs_uint(self.stake_reward_rate)
        if self._to_int(state.staked_mint) > 0 and elapsed > 0:
            rewards = (self._to_int(state.staked_mint) * rate * elapsed) // 1_000_000
            state.mint_balance = ARC4UInt64(self._to_int(state.mint_balance) + rewards)
        state.mint_balance = ARC4UInt64(self._to_int(state.mint_balance) - self._to_int(amount))
        state.staked_mint = ARC4UInt64(self._to_int(state.staked_mint) + self._to_int(amount))
        state.last_stake_timestamp = ARC4UInt64(now)
        self.player_states[sender] = state

    @abimethod
    def unstake_mint_tokens(self, amount: UInt64, sender: Account) -> None:
        state, exists = self.player_states.maybe(sender)
        if not exists or self._to_int(state.staked_mint) < self._to_int(amount):
            raise Exception("insufficient staked mint")
        now = 0
        elapsed = max(0, now - self._to_int(state.last_stake_timestamp))
        rate = self._gs_uint(self.stake_reward_rate)
        if self._to_int(state.staked_mint) > 0 and elapsed > 0:
            rewards = (self._to_int(state.staked_mint) * rate * elapsed) // 1_000_000
            state.mint_balance = ARC4UInt64(self._to_int(state.mint_balance) + rewards)
        state.staked_mint = ARC4UInt64(self._to_int(state.staked_mint) - self._to_int(amount))
        state.mint_balance = ARC4UInt64(self._to_int(state.mint_balance) + self._to_int(amount))
        state.last_stake_timestamp = ARC4UInt64(now)
        self.player_states[sender] = state

    @abimethod
    def award_achievement_nft(self, player: Account, nft_name: Bytes) -> None:
        state, exists = self.player_states.maybe(player)
        if not exists:
            state = PlayerState(ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0), ARC4UInt64(0))
        state.nfts_owned = ARC4UInt64(self._to_int(state.nfts_owned) + 1)
        self.player_states[player] = state

    @abimethod
    def _simulate_swap(self, player: Account, token_in: UInt64, token_out: UInt64, amount_in: UInt64) -> None:
        state, exists = self.player_states.maybe(player)
        if not exists:
            raise Exception("player not found")
        mint_id = self._gs_uint(self.mint_token_asa)
        spot_id = self._gs_uint(self.spot_token_asa)
        amt = self._to_int(amount_in)
        if int(token_in) == mint_id and int(token_out) == spot_id:
            if self._to_int(state.mint_balance) < amt:
                raise Exception("insufficient mint")
            state.mint_balance = ARC4UInt64(self._to_int(state.mint_balance) - amt)
            amount_out = (amt * self._gs_uint(self.mint_price_algo)) // max(1, self._gs_uint(self.spot_price_algo))
            state.spot_balance = ARC4UInt64(self._to_int(state.spot_balance) + amount_out)
        elif int(token_in) == spot_id and int(token_out) == mint_id:
            if self._to_int(state.spot_balance) < amt:
                raise Exception("insufficient spot")
            state.spot_balance = ARC4UInt64(self._to_int(state.spot_balance) - amt)
            amount_out = (amt * self._gs_uint(self.spot_price_algo)) // max(1, self._gs_uint(self.mint_price_algo))
            state.mint_balance = ARC4UInt64(self._to_int(state.mint_balance) + amount_out)
        else:
            raise Exception("unsupported swap pair")
        self.player_states[player] = state


def create_contract() -> GameFiDApp:
    return GameFiDApp()

