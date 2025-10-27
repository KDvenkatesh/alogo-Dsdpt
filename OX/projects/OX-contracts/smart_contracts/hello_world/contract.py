from algopy import (
    Account,
    ARC4Contract,
    arc4,
    BoxMap,
    Bytes,
    GlobalState,
    itxn,
    Txn,
    UInt64,
)
from algopy.op import itob

class GamesHub(ARC4Contract):
    """
    GamesHub: Entry fee, reward payout, leaderboard, coin collection game, and in-game store using box storage.
    """

    def _init_(self) -> None:  # <-- Corrected constructor name
        self.admin = GlobalState(Account)
        self.treasury_algo = GlobalState(UInt64)
        self.entry_fee = GlobalState(UInt64)
        self.reward_amount = GlobalState(UInt64)
        self.low_entry_fee = GlobalState(UInt64)
        self.item_price_mint = GlobalState(UInt64)
        self.player_algo_box = BoxMap(Bytes, UInt64, key_prefix=b"player_algo_")
        self.player_score_box = BoxMap(Bytes, UInt64, key_prefix=b"player_score_")
        self.player_mint_box = BoxMap(Bytes, UInt64, key_prefix=b"player_mint_")
        self.player_items_box = BoxMap(Bytes, UInt64, key_prefix=b"player_item_")

    @arc4.abimethod
    def create(
        self,
        entry_fee: UInt64,
        reward_amount: UInt64,
        low_entry_fee: UInt64,
        item_price_mint: UInt64,
    ) -> None:
        self.admin.value = Txn.sender
        self.treasury_algo.value = UInt64(0)
        self.entry_fee.value = entry_fee
        self.reward_amount.value = reward_amount
        self.low_entry_fee.value = low_entry_fee
        self.item_price_mint.value = item_price_mint

    @arc4.abimethod
    def add_mint_tokens(self, player: Account, amount: UInt64) -> UInt64:
        """
        Add MINT tokens to a player's balance.
        Only admin can add tokens.
        Client must pass box_reference = b"player_mint_" + player.bytes
        Returns the player's new MINT balance.
        """
        assert Txn.sender == self.admin.value, "Only admin can add MINT tokens"

        key = player.bytes
        current_balance = self.player_mint_box.get(key, default=UInt64(0))
        new_balance = current_balance + amount
        self.player_mint_box[key] = new_balance

        return new_balance

    @arc4.abimethod
    def set_item_price(self, price: UInt64) -> None:
        assert Txn.sender == self.admin.value, "Only admin can set price"
        self.item_price_mint.value = price

    @arc4.abimethod
    def buy_item_with_mint(self, player: Account, item_id: UInt64) -> UInt64:
        """
        Player buys an item using MINT tokens.
        Client must pass box_reference = b"player_mint_" + player.bytes
        and box_reference = b"player_item_" + player.bytes + itob(item_id).
        Returns the player's new MINT balance.
        """
        key = player.bytes
        price = self.item_price_mint.value
        mint_balance = self.player_mint_box.get(key, default=UInt64(0))
        assert mint_balance >= price, "Insufficient MINT tokens"
        self.player_mint_box[key] = mint_balance - price
        item_key = key + itob(item_id)
        self.player_items_box[item_key] = UInt64(1)
        return self.player_mint_box[key]

    @arc4.abimethod
    def has_item(self, player: Account, item_id: UInt64) -> UInt64:
        """
        Check if the player owns the item.
        Client must pass box_reference = b"player_item_" + player.bytes + itob(item_id).
        """
        item_key = player.bytes + itob(item_id)
        return self.player_items_box.get(item_key, default=UInt64(0))

    @arc4.abimethod
    def set_low_entry_fee(self, fee: UInt64) -> None:
        assert Txn.sender == self.admin.value, "Only admin can set fee"
        self.low_entry_fee.value = fee

    @arc4.abimethod
    def deposit_algo(self, sender: Account, amount: UInt64) -> None:
        key = sender.bytes
        current = self.player_algo_box.get(key, default=UInt64(0))
        self.player_algo_box[key] = current + amount
        self.treasury_algo.value = self.treasury_algo.value + amount

    @arc4.abimethod
    def enter_game(self, player: Account) -> None:
        key = player.bytes
        current = self.player_algo_box.get(key, default=UInt64(0))
        fee = self.entry_fee.value
        assert current >= fee, "Insufficient ALGO for entry fee"
        self.player_algo_box[key] = current - fee
        self.treasury_algo.value = self.treasury_algo.value + fee

    @arc4.abimethod
    def start_coin_collection_game(self, player: Account) -> None:
        key = player.bytes
        current = self.player_algo_box.get(key, default=UInt64(0))
        fee = self.low_entry_fee.value
        assert current >= fee, "Insufficient ALGO for entry fee"
        self.player_algo_box[key] = current - fee
        self.treasury_algo.value = self.treasury_algo.value + fee

    @arc4.abimethod
    def end_coin_collection_game(
        self, player: Account, coins_collected: UInt64
    ) -> None:
        key = player.bytes
        units = coins_collected // UInt64(10000)
        mint_award = units * UInt64(5)
        if mint_award > UInt64(0):
            mint_current = self.player_mint_box.get(key, default=UInt64(0))
            self.player_mint_box[key] = mint_current + mint_award

    @arc4.abimethod
    def win_game(self, player: Account) -> None:
        key = player.bytes
        current = self.player_algo_box.get(key, default=UInt64(0))
        score = self.player_score_box.get(key, default=UInt64(0))
        reward = self.reward_amount.value
        assert self.treasury_algo.value >= reward, "Treasury insufficient"
        self.player_algo_box[key] = current + reward
        self.treasury_algo.value = self.treasury_algo.value - reward
        self.player_score_box[key] = score + UInt64(1)
        mint_current = self.player_mint_box.get(key, default=UInt64(0))
        mint_new = mint_current + UInt64(5)
        self.player_mint_box[key] = mint_new
        thousand = UInt64(1000)
        algo_per_thousand = UInt64(1)
        if mint_new >= thousand:
            num_thousands = mint_new // thousand
            mint_remaining = mint_new % thousand
            algo_credit = num_thousands * algo_per_thousand
            self.player_mint_box[key] = mint_remaining
            algo_balance = self.player_algo_box.get(key, default=UInt64(0))
            self.player_algo_box[key] = algo_balance + algo_credit
            self.treasury_algo.value = self.treasury_algo.value - algo_credit

    @arc4.abimethod
    def withdraw_algo(self, player: Account, amount: UInt64) -> None:
        """
        Withdraw ALGO for a player.
        Requires box_reference = b"player_algo_" + player.bytes.
        """
        key = player.bytes
        current = self.player_algo_box.get(key, default=UInt64(0))
        assert current >= amount, "Insufficient balance"
        assert self.treasury_algo.value >= amount, "Treasury insufficient"
        self.player_algo_box[key] = current - amount
        self.treasury_algo.value = self.treasury_algo.value - amount
        itxn.Payment(receiver=player, amount=amount).submit()

    @arc4.abimethod
    def get_score(self, player: Account) -> UInt64:
        key = player.bytes
        return self.player_score_box.get(key, default=UInt64(0))

    @arc4.abimethod
    def get_balance(self, player: Account) -> UInt64:
        key = player.bytes
        return self.player_algo_box.get(key, default=UInt64(0))

    @arc4.abimethod
    def get_mint_balance(self, player: Account) -> UInt64:
        key = player.bytes
        return self.player_mint_box.get(key, default=UInt64(0))
