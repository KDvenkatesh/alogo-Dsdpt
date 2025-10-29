# alogo-Dsdpt

🕹️ GamesHub ARC4 Smart Contract
Built with AlgoPy
 | Designed for GameFi DApps on Algorand
📘 Overview

GamesHub is an ARC4-compatible Algorand smart contract designed for blockchain-based gaming platforms.
It handles player accounts, entry fees, reward distribution, tokenized gameplay (MINT tokens), item purchases, and a leaderboard system — all on-chain using Box storage for scalability.

It can serve as the backend logic for a GameFi hub where users:

Pay ALGO to enter games

Win ALGO and MINT tokens as rewards

Buy in-game items with MINT tokens

Track leaderboard scores

Convert MINT to ALGO automatically through gameplay

⚙️ Contract Structure
Component	Type	Description
admin	GlobalState(Account)	Deployer/administrator of the contract
treasury_algo	GlobalState(UInt64)	Total ALGO held by the contract
entry_fee	GlobalState(UInt64)	Fee required to enter a main game
reward_amount	GlobalState(UInt64)	Reward paid to winners
low_entry_fee	GlobalState(UInt64)	Entry fee for smaller games (e.g., coin collection)
item_price_mint	GlobalState(UInt64)	Price (in MINT tokens) for in-game items
player_algo_box	BoxMap(Bytes, UInt64)	Stores each player’s ALGO balance
player_score_box	BoxMap(Bytes, UInt64)	Stores each player’s total wins/score
player_mint_box	BoxMap(Bytes, UInt64)	Stores each player’s MINT token balance
player_items_box	BoxMap(Bytes, UInt64)	Tracks items owned by each player
🚀 Key Features
🪙 Token & Treasury Management

Deposit ALGO into the game using deposit_algo.

Withdraw ALGO (treasury-backed) using withdraw_algo.

MINT tokens managed by the admin and rewarded automatically through gameplay.

🎮 Game Mechanics

Enter main game: Deducts ALGO entry_fee.

Start mini-game (coin collection): Deducts low_entry_fee.

Win rewards: Increases player ALGO and MINT balance.

🏆 Progression & Rewards

Collecting coins grants MINT tokens based on performance.

Winning games increases leaderboard score and balance.

MINT automatically converts to ALGO every 1000 tokens.

🛒 In-Game Store

Players can buy items with MINT tokens using buy_item_with_mint.

Ownership verified with has_item.

Admin can set item prices using set_item_price.

📦 ABI Methods
🧩 Setup & Configuration
Method	Description
create(entry_fee, reward_amount, low_entry_fee, item_price_mint)	Initializes contract parameters and admin
set_item_price(price)	Admin-only: sets the price of store items
set_low_entry_fee(fee)	Admin-only: updates mini-game entry fee
👤 Player Economy
Method	Description
deposit_algo(sender, amount)	Deposits ALGO into player balance
withdraw_algo(player, amount)	Withdraws ALGO (via inner transaction)
add_mint_tokens(player, amount)	Admin-only: adds MINT tokens to player
get_balance(player)	Returns ALGO balance
get_mint_balance(player)	Returns MINT balance
🕹️ Game Logic
Method	Description
enter_game(player)	Deducts entry_fee from player ALGO
start_coin_collection_game(player)	Starts low-fee mini-game
end_coin_collection_game(player, coins_collected)	Rewards MINT tokens based on coins
win_game(player)	Gives ALGO + MINT reward and updates score
get_score(player)	Returns total number of wins
🛍️ Store & Inventory
Method	Description
buy_item_with_mint(player, item_id)	Buys an item with MINT tokens
has_item(player, item_id)	Checks ownership of an item
🧠 Logic Highlights

Box storage is used for scalable and efficient state tracking per player.

MINT-to-ALGO auto conversion:
Every 1000 MINT tokens → 1 ALGO, credited automatically in win_game.

Safe withdrawals using itxn.Payment() ensure no treasury overflow.

Admin verification on sensitive functions like minting and price settings.

🧩 Deployment Steps
1️⃣ Prerequisites

Install AlgoKit and AlgoPy:

pip install algopy
algokit init


Make sure your Python environment supports ARC4 smart contracts.

2️⃣ Build Contract
poetry run python -m smart_contracts build

3️⃣ Deploy

Deploy the contract via AlgoKit CLI or any ARC4-compatible deployer script.

4️⃣ Interact

Use goal, AlgoKit, or a React frontend with Algorand SDK / WalletConnect to call ABI methods.

🧰 Example Frontend Use (Pseudo-code)
await contract.methods.enter_game(player).call({
  boxReferences: [ { name: "player_algo_" + playerAddress } ],
});

await contract.methods.buy_item_with_mint(player, itemId).call({
  boxReferences: [
    { name: "player_mint_" + playerAddress },
    { name: "player_item_" + playerAddress + itob(itemId) },
  ],
});

🔐 Security Considerations

Admin-only methods are strictly validated using Txn.sender == self.admin.value.

Treasury balance checks prevent overdrawing.

Player balances use box isolation for secure state management.

Always validate box_references in client calls.

🏁 Summary
Feature	Description
🎮 Game Entry	Pay ALGO to play
🏆 Rewards	Earn ALGO + MINT
💎 Store	Buy items with MINT
📊 Leaderboard	Track player wins
🔄 MINT to ALGO	Automatic conversion
🔐 Secure Admin	Controlled game settings
💡 Author

K Dhanu Venkatesh
Blockchain Developer | GameFi Enthusiast | Algorand Innovator
