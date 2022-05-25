extensions [array table]

;*****************************************************************************************************
;Global Variables
;*****************************************************************************************************
;------------------------------------------------------------------------------
; Variables available globally
;------------------------------------------------------------------------------
Globals [
;  UseSeed                  ;Whether to use the manual random number seed to override the default seed
;  RanSeed                  ;Manual random number seed to use, if override is chosen
  ActSeed                  ;Actual random number seed used (may be adjusted for behaviorspace-run-number)
  price                    ;Current price of the asset
  buyQueue                 ;Bid side of the order book
  sellQueue                ;Ask side of the order book
  orderNumber
  tradeWipeQueue           ;Coding wipe queue for transactions
  tradeMatch               ;Trade match id variable
  currentAsk               ;Current best ask price
  currentBid               ;Current best bid price
  numberBid                ;Plotting variable
  numberAsk                ;Plotting variable
  volume                   ;Single-agent volume of executed trades
  volatility               ;Volatility of the market
  currentPriceVol          ;Helps determine the price volatility
  totalVolume              ;Total volume of executed trades in the market
  currentVol               ;Most recent volume executed
  movingAverage            ;Moving average price of the asset for 1 min (600 ticks)
  currentMA                ;Most recent moving average price
  movingAverageV           ;Moving average volume of the asset for 1 min (600 ticks)
  currentMAV               ;Most recent moving average volume
  currentBQD               ;Current bid book depth
  currentSQD               ;Current ask book depth
  pastMA                   ;Previous moving average price
  priceReturns             ;List of all price returns
  transactionCost          ;Cost of trading
  aggressiveBid            ;Number of market orders to buy
  aggressiveAsk            ;Number of market orders to sell
  minPriceValue            ;Minimum price of asset, used for measuring flash crash effect
  randNumOT
  pastPrices               ;Keeps track of previous prices
  period                   ;Allows tracking of a sequence in a trade strategy
  tradeWipeQueueB          ;List of all bid trades that occured in a tick period, used for updating the order book
  tradeWipeQueueA          ;List of all ask trades that occured in a tick period, used for updating the order book
  arrayQ                   ;Array contraining the quantities for each order
  tradeExNumber            ;Helps track the sequence of actions in the audit trail book
  traderListNumbers        ;Used in verfying that each trader has a unique trader account number
  currentBuyInterest
  currentSellInterest
  currentBuyInterestPrice
  currentSellInterestPrice
  maxBuyInterest
  priceVolatilityVar       ;Volatility variable, in order to create trends in volatility
  BuyOrderQueue
  SellOrderQueue
  numberOrderBid
  numberOrderAsk
  currentOrderAsk
  currentOrderBid
  MatchID
  marketImpactValue
  timeserieslist
  timeserieslistcount
  resethillclimbto50       ;Used for Liquidity Demander agents
  Batching
  Batch_Length
  allOrders                ;List of all orders and order_updates hatched in the current tick cycle
  list_orders              ;List of all orders (but not order_updates) available at the end of current tick cycle
  list_traders             ;List of all traders at the end of the current tick cycle, for the inventory report

  ;These variables are for external input/output, and are not currently used (commented out everywhere)
  ;TODO: ##EXTERNAL_IO##
  ;LogFilePath              ;The local filesytem path to the log files emitted by the simulation
  ;LogFileRoot              ;A base filename for each log file. E.g., "MyRoot" generates "MyRootPrice.csv", "MyRootLbook.csv", etc.
  ;LOG_BehSpc_suffix        ;A suffix of the form "_r<N>_", (N is the BehaviorSpace run number) to distinguish log files (e.g., "MyRoot_r1_Lbook.csv")
  ;LOG_Audit                ;Full path+filename for the audit log, "OrderBook.csv"
  ;LOG_LBook                ;Full path+filename for the lbook log, "LBook.csv"
  ;LOG_Depth                ;Full path+filename for the depth log, "OrderBookDepth.csv"
  ;LOG_AgentFile            ;Full path+filename for the agent log, "AgentData.csv"
  ;LOG_PriceFile            ;Full path+filename for the price log, "Price.csv"
  ;LOG_TraderFile           ;Full path+filename for the trader log, "Trader.csv"
]

;These global variables should be defined/set in the interface
;   #_MktMkr MktMkr_OrderSizeMult MktMkr_TradeLength MktMkr_ArrivalRate   MktMkr_InvLimit
;   #_LiqDem LiqDem_OrderSizeMult LiqDem_TradeLength LiqDem_ArrivalRate   LiqDem_ProbBuy timeseriesvalue timeseries
;   #_LiqSup LiqSup_OrderSizeMult LiqSup_TradeLength LiqSup_ArrivalRate   LiqSup_PctPriceChange
;   #_HftTdr                      HftTdr_TradeLength
;   #_OppTdr                      OppTdr_TradeLength
;   #_AbsTdr
;   #_RatTdr                                                              RatTdr_InvRatio RatTdr_ImbalRatio p_weight
;   #_FrcSal                                                              FrcSal_QuantSale FrcSal_PerStartExec FrcSal_PerEndExec
;   #_SpfTdr                                                              SpfTdr_BalDistance
;code by Mark Paddrik


;*****************************************************************************************************
;Agents' Variables
;*****************************************************************************************************

;------------------------------------------------------------------------------
; Variables available to all turtles
;------------------------------------------------------------------------------
turtles-own [
  movingAverageDIS         ;Moving average difference between the moviing average price and the current price, used as a threshold for a trader
  totalCanceled            ;Total number of trades canceled or modified by a trader
  reversion                ;Price reversion mechanism to remove positions from market makers and high frequency traders
  typeOfTrader             ;Indicates the type of trader
  traderNumber             ;Random number indicating a trader in the order book
  tradeStatus              ;Current trade status (buy/sell/bought/sold/canceled) in the order book
  tradeQuantity            ;Current quantity trading in the order book
  tradeOrderNumber         ;Number of the Order that is currently in the order book
  speed                    ;Frequency of trading for this trader
  tradeSpeedAdjustment     ;Random delay in each trader's trading speed, based on class of trader
  tradePrice               ;Price of the current trade in the order book
  tradeOrderForm           ;Order book info
  countticks               ;Duration a trade has been in the book
  sharesOwned              ;Number of shares outstanding
  tradeAccount             ;Profitability of the trader
  totalBought              ;Total number shares of bought
  totalSold                ;Total number shares sold
  averageBoughtPrice       ;Average buy price
  averageSoldPrice         ;Average sell price
  checkTraderNumber        ;Flag to verify that each trader has a unique trader account number
  buysell                  ;Indicates in the audit trail whether a trader is on the Buy (B) or Sell (S) side of the book
  modify                   ;Determines if an order has been modified
  pattern
  direct
  move
  counter
]

;------------------------------------------------------------------------------
; Structure of orders -- a special subtype of turtles
;------------------------------------------------------------------------------
breed [orders an-order]
orders-own [
  OrderID                  ;Sequential order identifier (counts from 0 for each trader)
  OrderPrice               ;Limit price for the order
  PriceOrder               ;Clever index for price-time priority sorting: (OrderPrice * 100000000000) + OrderID
  OrderTime                ;Time (in ticks) the order was issued
  OrderTraderID            ;The traderNumber of the trader placing this order
  OrderQuantity            ;Requested tradeQuantity for this order
  OrderB/A                 ;Buy/sell indicator ("Buy" or "Sell")
  TraderWho                ;NetLogo "who" number of the trader placing this order
  TraderWhoType            ;Labeled typeOfTrader of the trader placing this order
  HON1                     ;No one knows what this is (TODO!!)
  HON2                     ;No one knows what this is (TODO!!)
]

breed [order_updates an-order_update]
order_updates-own [
  OrderID                  ;Sequential order identifier (counts from 0 for each trader)
  OrderPrice               ;Limit price for the order
  OrderTime                ;Time (in ticks) the order was issued
  OrderTraderID            ;The traderNumber of the trader placing this order
  OrderQuantity            ;Requested tradeQuantity for this order
  OrderB/A                 ;Buy/sell indicator ("Buy" or "Sell")
  TraderWho                ;NetLogo "who" number of the trader placing this order
  TraderWhoType            ;Labeled typeOfTrader of the trader placing this order
]

;------------------------------------------------------------------------------
; Structure of traders -- a special subtype of turtles
;------------------------------------------------------------------------------
breed [traders a-trader]
traders-own [
  openOrders               ;List of open orders for this trader
  PriceOrder               ;Appears to be unused (TODO!!)
  OrderPositionDesired     ;Appears to be unused (TODO!!)
]

;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;==============================================================================
;==============================================================================
;==============================================================================
;============ GENERAL SIMULATION SETUP AND RUN ================================
;==============================================================================
;==============================================================================
;==============================================================================

;//////////////////////////////////////////////////////////////////////////////
to setup
  __clear-all-and-reset-ticks

;  ifelse (UseSeed = true)
;     [ set ActSeed (RanSeed + behaviorspace-run-number) ]
;     [ set ActSeed (new-seed) ]
  random-seed ActSeed

  setup-economy
  file-close-all
  set currentMA 100
  set volatility [1 2 3 5 7]
  set pastPrices [1 2 3 5 7]
  set movingAverage []
  set movingAverageV []
  set priceReturns []
  set currentPriceVol 1
  set currentBQD 2
  set currentSQD 2
  set transactionCost 0
  set pastMA 400
  set LiqDem_ProbBuy 49

  set currentOrderBid 399
  set currentOrderAsk 401
  set price 400

  set timeserieslist [200 300 200 0 200 500 300 0 -100 100 100 0 0]
  set timeserieslistcount 0
  set resethillclimbto50 0

;  my-setup-plots
  set arrayQ array:from-list n-values 10000 ["B"]
  set period 0
  set tradeExNumber 0
  set numberAsk []
  set numberBid []

  set BuyOrderQueue []
  set SellOrderQueue []
  set numberOrderAsk []
  set numberOrderBid []

;  TODO: ##EXTERNAL_IO##
;  set LOG_BehSpc_suffix ""
;  if (behaviorspace-run-number > 0)
  ; if (true)
;    [ set LOG_BehSpc_suffix (word "_r" behaviorspace-run-number "_")]

;  TODO: ##EXTERNAL_IO##
;  set LogFilePath ""
;  set LogFileRoot "LOG"

;  TODO: ##EXTERNAL_IO##
;  set LOG_Audit      (word LogFilePath LogFileRoot LOG_BehSpc_suffix "OrderBook.csv")
;  set LOG_LBook      (word LogFilePath LogFileRoot LOG_BehSpc_suffix "LBook.csv")
;  set LOG_Depth      (word LogFilePath LogFileRoot LOG_BehSpc_suffix "OrderBookDepth.csv")
;  set LOG_AgentFile  (word LogFilePath LogFileRoot LOG_BehSpc_suffix "AgentData.csv")
;  set LOG_PriceFile  (word LogFilePath LogFileRoot LOG_BehSpc_suffix "Price.csv")
;  set LOG_TraderFile (word LogFilePath LogFileRoot LOG_BehSpc_suffix "Trader.csv")

;  TODO: ##EXTERNAL_IO##
;  carefully [file-delete LOG_Audit][]
;  carefully [file-delete LOG_LBook][]
;  carefully [file-delete LOG_Depth][]
;  carefully [file-delete LOG_AgentFile][]
;  carefully [file-delete LOG_PriceFile][]
;  carefully [file-delete LOG_TraderFile][]

;  TODO: ##EXTERNAL_IO##
;  carefully [writeFileTitles][]
;  carefully [writeFileTitleDepth][]
;  carefully [writeFileTitleAgent][]
;  carefully [writeFileTitleBook][]
;  carefully [writeFileTitlePrice][]
;  carefully [writeFileTitleTrader][]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to setup-economy
  ;Initial Model and Agent Conditions

  ;; turtles procedure for setup
  set traderListNumbers [0]
  create-traders #_MktMkr [MktMkr_Setup]
  create-traders #_LiqDem [LiqDem_Setup]
  create-traders #_LiqSup [LiqSup_Setup]
  create-traders #_HftTdr [HftTdr_Setup]
  create-traders #_OppTdr [OppTdr_Setup]
  create-traders #_AbsTdr [AbsTdr_Setup]
  create-traders #_RatTdr [RatTdr_Setup]
  set #_FrcSal 0                          ; <== HACK! Ensure zero forced-sale traders
  create-traders #_FrcSal [FrcSal_Setup]
  create-traders #_SpfTdr [SpfTdr_Setup]

  set allOrders []

  set buyQueue []
  set sellQueue []
  set tradeWipeQueue []
  set tradeWipeQueueB []
  set tradeWipeQueueA []
  set list_traders []
  ask traders [
    set list_traders lput self list_traders
    if(ticks = 0) [
      checkTraderNumberUnique
      ifelse (checkTraderNumber = 1) [
        set traderListNumbers lput traderNumber traderListNumbers
      ] [
        checkTraderNumberUnique
      ]
    ]
  ]
  
  ; Sort the traders by who number, creating a list
  ;set list_traders sort traders

end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to checkTraderNumberUnique
  let countTradersintradelist length traderListNumbers - 1
  set traderNumber  10 + random 9990
  let countTraderNumber 0
  set checkTraderNumber 1
  loop [
    if(item countTraderNumber traderListNumbers = traderNumber) [
      set checkTraderNumber 0
    ]
    if(countTraderNumber = countTradersintradelist) [
      stop
    ]
    set countTraderNumber (countTraderNumber + 1)
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to go
  ;Function run for every tick of the model to advance one time step ahead

  ; The allOrders list holds all orders and order_updates hatched this tick
  ask order_updates [
    die
  ]
  set allOrders []
;  TestFOOBAR "FOO"

  set currentBuyInterest 0
  set currentSellInterest 0
  set currentBuyInterestPrice 0
  set currentSellInterestPrice 0

  if ((ticks - 5000) mod 1440 = 1439 and ticks > 5000) [
    set timeserieslistcount (timeserieslistcount + 1)
  ]

  if (ticks mod 10 = 0) [
    set aggressiveBid 0
    set aggressiveAsk 0
  ]

  ask traders [

    set countticks (countticks + 1)
    set counter (counter + 1)

;    TestFOOBAR self

    if (typeOfTrader = "LiquidityDemander") [
      if countticks >= (LiqDem_TradeLength + tradeSpeedAdjustment) [
        set tradeStatus "Transact"
        if(ticks > 5000) [
          set totalCanceled (totalCanceled + tradeQuantity)
        ]
        set speed int(random-poisson LiqDem_ArrivalRate) + 1
      ]
    ]

    if (typeOfTrader = "MarketMakers") [
      if countticks >= (MktMkr_TradeLength + tradeSpeedAdjustment)[
        set tradeStatus "Transact"
        set speed int(random-poisson MktMkr_ArrivalRate) + 2
      ]
    ]

    if (typeOfTrader = "LiquiditySupplier") [
      if countticks >= (LiqSup_TradeLength + tradeSpeedAdjustment)  [
        set tradeStatus "Transact"
        if(ticks > 5000) [
          set totalCanceled (totalCanceled + tradeQuantity)
        ]
        set speed int(random-poisson LiqSup_ArrivalRate) + 1
      ]
    ]

    if (typeOfTrader = "ForcedSale" and FrcSal_QuantSale > 0) [
      if ((countticks >= (5 + tradeSpeedAdjustment)) and (FrcSal_PerStartExec < ticks) and (FrcSal_PerEndExec >= ticks)) [
        set tradeStatus "Transact"
        set speed 5
      ]
    ]

    if (typeOfTrader = "HighFrequency") [
      if countticks >= (HftTdr_TradeLength + tradeSpeedAdjustment)  [
        set tradeStatus "Transact"
        if(ticks > 5000) [
          set totalCanceled (totalCanceled + tradeQuantity)
        ]
        set speed (random-poisson 3) + 1
      ]
    ]

    if (typeOfTrader = "OpportunisticTraders") [
      if countticks >= (OppTdr_TradeLength + tradeSpeedAdjustment)  [
        set tradeStatus "Transact"
        if(ticks > 5000) [
          set totalCanceled (totalCanceled + tradeQuantity)
        ]
        set speed (random-poisson 300) + 1
      ]
    ]

    if (typeOfTrader = "absolutetrader") [
      if countticks >= (100)  [
        set tradeStatus "Transact"
        if(ticks > 5000) [
          set totalCanceled (totalCanceled + tradeQuantity)
        ]
        set speed (random-poisson 200) + 1
      ]
    ]

    if (typeOfTrader = "ratiotrader") [
      if countticks >= (10)  [
        set tradeStatus "Transact"
        if(ticks > 5000) [
          set totalCanceled (totalCanceled + tradeQuantity)
        ]
        set speed 1
      ]
    ]

    if (typeOfTrader = "spoofer") [
      if (pattern = "abuy") [ set move 100 ]
      if (pattern = "abuyafter") [ set move 2 ]
      if (pattern = "abuycancel") [ set move 10 ]
      if (pattern = "asell") [ set move 100 ]
      if (pattern = "asellafter") [ set move 2 ]
      if (pattern = "asellcancel") [ set move 10 ]

      if countticks >= (move) [
        set tradeStatus "Transact"
        if(ticks > 5000) [
          set totalCanceled (totalCanceled + tradeQuantity)
        ]
        set speed 1
      ]
    ]

    set tradeAccount ((sharesOwned * ( price / 4) - averageBoughtPrice * totalBought + averageSoldPrice * totalSold) - (transactionCost * (totalBought + totalSold)))

    if((typeOfTrader = "spoofer" or typeOfTrader = "LiquidityDemander" or typeOfTrader = "absolutetrader" or typeOfTrader = "LiquiditySupplier" or typeOfTrader = "MarketMakers"  or typeOfTrader = "HighFrequency" or typeOfTrader = "OpportunisticTraders" or typeOfTrader = "ratiotrader") and tradeStatus = "Buy" and tradeQuantity > 0)[
      set currentBuyInterestPrice ((currentBuyInterestPrice * currentBuyInterest + tradeQuantity * tradePrice) / (currentBuyInterest + tradeQuantity))
      set currentBuyInterest (currentBuyInterest + tradeQuantity)
    ]

    if((typeOfTrader = "spoofer" or typeOfTrader = "LiquidityDemander" or typeOfTrader = "LiquiditySupplier" or typeOfTrader = "absolutetrader" or typeOfTrader = "MarketMakers" or typeOfTrader = "HighFrequency" or typeOfTrader = "OpportunisticTraders"  or typeOfTrader = "ratiotrader") and tradeStatus = "Sell" and tradeQuantity > 0)[
      set currentSellInterestPrice ((currentSellInterestPrice * currentSellInterest + tradeQuantity * tradePrice) / (currentSellInterest + tradeQuantity))
      set currentSellInterest (currentSellInterest + tradeQuantity)
    ]


    if (tradeStatus = "Transact")[
      if countticks > (speed + tradeSpeedAdjustment)  [

        set countticks 0
        set modify 0

        if typeOfTrader = "LiquidityDemander" [
          LiqDem_strategy
        ]
        if typeOfTrader = "spoofer" [
          SpfTdr_strategy
        ]
        if typeOfTrader = "MarketMakers" [
          MktMkr_strategy
        ]
        if typeOfTrader = "LiquiditySupplier" [
          LiqSup_strategy
        ]
        if typeOfTrader = "ForcedSale" [
          FrcSal_strategy
        ]
        if typeOfTrader = "HighFrequency" [
          HftTdr_strategy
        ]
        if typeOfTrader = "OpportunisticTraders" [
          OppTdr_strategy
        ]
        if typeOfTrader = "absolutetrader" [
          AbsTdr_strategy
        ]
        if typeOfTrader = "ratiotrader" [
          RatTdr_strategy
        ]

        if (tradeStatus = "Buy") [
           set buysell "B"
        ]
        if (tradeStatus = "Sell") [
           set buysell "S"
        ]

        if (tradePrice <= currentOrderBid and tradeStatus = "Buy") [
          set aggressiveBid (aggressiveBid + tradeQuantity)
        ]
        if (tradePrice >= currentOrderAsk and tradeStatus = "Sell") [
          set aggressiveAsk (aggressiveAsk + tradeQuantity)
        ]
      ]
      ; TODO: It appears this variable is never used -- delete?
      let transactionVar 0
    ]

    if (Batching = TRUE) [
      ;;;;; Batching Code
      if (ticks > 5000 and remainder ticks Batch_Length  = 0 ) [
        transactionOrder
      ]
    ]
    if (Batching = FALSE) [
      ;;;;; Regular Coding
      if (ticks > 5000 ) [
        transactionOrder
      ]
    ]

  ]

  if ( count orders with [OrderB/A = "Buy"] > 0 ) [
    set numberOrderBid []
;    histoSetupTestBuy
;    setup-plot2
  ]

  if ( count orders with [OrderB/A = "Sell"] > 0 ) [
    set numberOrderAsk []
;    histoSetupTestSell
  ]

;  do-plots

;  if(ticks >= 5000) [
;    if((ticks - 4700) mod 600 = 0 ) [
;      calculatePriceReturns
;    ]
;  ]

;  if(ticks > 12000) [
;    set minPriceValue min movingAverage
;  ]
;  if(DepthFile = true and ticks > 5999)[
;    writetofiledepth
;  ]
;  if(AgentFile = true and ticks > 5999)[
;    writetofileagent
;  ]
;  if(obfile = true and ticks > 5999)[
;    writetofileBook
;  ]
;  if(pricefile = true and ticks > 5999)[
;    writetofilePrice
;  ]
;  if(traderfile = true and ticks > 5999)[
;    writetofileTrader
;  ]

  ; Sort the current orders (the order book) by who number, creating a list
  set list_orders sort orders
  
  tick

end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to calculatePriceReturns
  set priceReturns lput (ln((item (length movingAverage - 1) movingAverage) / (item (length movingAverage - 30) movingAverage)))  priceReturns
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to transactionOrder
  ;Function for transacting Trades to be run in the Market
  if ( count orders with [OrderB/A = "Buy"] > 0 and count orders with [OrderB/A = "Sell"] > 0) [
    let firstInBuyQueue first (sort-on [(- PriceOrder)] orders with [OrderB/A = "Buy"] )
    let firstInSellQueue first (sort-on [PriceOrder] orders with [OrderB/A = "Sell"])

    let quantityDiff 0
    let orderBidID 0
    let orderAskID 0
    let traderBid 0
    let traderAsk 0

    let traderBidNum 0
    let traderAskNum 0

    let traderBidType 0
    let traderAskType 0

    let orderQuantityBid 0
    let orderQuantityAsk 0

    let orderHON1Bid 0
    let orderHON2Bid 0
    let orderHON1Ask 0
    let orderHON2Ask 0

    ask firstInBuyQueue [
      set currentOrderBid OrderPrice
      set quantityDiff OrderQuantity
      set orderQuantityBid OrderQuantity
      set orderBidID OrderID
      set traderBid TraderWho
      set orderHON1Bid HON1
      set orderHON2Bid HON2
    ]

    ask firstInSellQueue [
      set currentOrderAsk OrderPrice
      set quantityDiff (quantityDiff - OrderQuantity)
      set orderQuantityAsk OrderQuantity
      set orderAskID OrderID
      set traderAsk TraderWho
      set orderHON1Ask HON1
      set orderHON2Ask HON2
    ]

    if (currentOrderAsk <= currentOrderBid) [
      if ( quantityDiff = 0 ) [

        ask traderBid [
          set openorders remove firstInBuyQueue openorders
          set traderBidNum traderNumber
          set traderBidType typeOfTrader
        ]
        ask traderAsk [
          set openorders remove firstInSellQueue openorders
          set traderAskNum traderNumber
          set traderAskType typeOfTrader
        ]
        ask firstInBuyQueue [ die ]
        ask firstInSellQueue [ die ]

        if orderBidID > orderAskID [
          set price currentOrderAsk
        ]
        if orderBidID < orderAskID [
          set price currentOrderBid
        ]

;        if (AuditTrail = true) [
;          set MatchID (MatchID + 1)
;          writetofile orderBidID "Bought" price orderQuantityBid traderBidType traderBidNum 1 MatchID orderHON1Bid orderHON2Bid
;          writetofile orderAskID "Sold" price orderQuantityAsk traderAskType traderAskNum 2 MatchID orderHON1Ask orderHON2Ask
;        ]
        hatch-order_updates 1 [Order_Update orderBidID price "Bought" traderBidNum orderQuantityBid traderBid traderBidType]
        hatch-order_updates 1 [Order_Update orderAskID price "Sold"   traderAskNum orderQuantityAsk traderAsk traderAskType]

        ask traderBid [
          set sharesOwned (sharesOwned + orderQuantityBid)
          set averageBoughtPrice ((averageBoughtPrice * totalBought + (price / 4) * orderQuantityBid) / (totalBought + orderQuantityBid))
          set totalBought (totalBought + orderQuantityBid)
        ]
        ask traderAsk [
          set sharesOwned (sharesOwned - orderQuantityAsk)
          set averageSoldPrice ((averageSoldPrice * totalSold + (price / 4) * orderQuantityAsk) / (totalSold + orderQuantityAsk))
          set totalSold (totalSold + orderQuantityAsk)
        ]
        set volume (volume + orderQuantityAsk)

      ]

      if ( quantityDiff > 0 ) [

        ask firstInBuyQueue [
          set OrderQuantity quantityDiff
        ]
        ask traderBid [
          set traderBidNum traderNumber
          set traderBidType typeOfTrader
        ]
        ask traderAsk [
          set openorders remove firstInSellQueue openorders
          set traderAskNum traderNumber
          set traderAskType typeOfTrader
        ]
        ask firstInSellQueue [
          die
        ]

        if orderBidID > orderAskID [
          set price currentOrderAsk
        ]
        if orderBidID < orderAskID [
          set price currentOrderBid
        ]

;        if(AuditTrail = true)[
;          set MatchID (MatchID + 1)
;          writetofile orderBidID "Bought" price orderQuantityAsk traderBidType traderBidNum 1 MatchID orderHON1Bid orderHON2Bid
;          writetofile orderAskID "Sold" price orderQuantityAsk traderAskType traderAskNum 2 MatchID orderHON1Ask orderHON2Ask
;        ]
        hatch-order_updates 1 [Order_Update orderBidID price "Bought" traderBidNum orderQuantityAsk traderBid traderBidType]
        hatch-order_updates 1 [Order_Update orderAskID price "Sold"   traderAskNum orderQuantityAsk traderAsk traderAskType]

        ask traderBid [
          set sharesOwned (sharesOwned + orderQuantityAsk)
          set averageBoughtPrice ((averageBoughtPrice * totalBought + (price / 4) * orderQuantityAsk) / (totalBought + orderQuantityAsk))
          set totalBought (totalBought + orderQuantityAsk)
        ]
        ask traderAsk [
          set sharesOwned (sharesOwned - orderQuantityAsk)
          set averageSoldPrice ((averageSoldPrice * totalSold + (price / 4) * orderQuantityAsk) / (totalSold + orderQuantityAsk))
          set totalSold (totalSold + orderQuantityAsk)
        ]
        set volume (volume + orderQuantityAsk)

        transactionOrder
      ]

      if ( quantityDiff < 0 ) [

        ask traderBid [
          set openorders remove firstInBuyQueue openorders
          set traderBidNum traderNumber
          set traderBidType typeOfTrader
        ]
        ask firstInSellQueue [
          set OrderQuantity ( -1 * quantityDiff)
        ]
        ask traderAsk [
          set traderAskNum traderNumber
          set traderAskType typeOfTrader
        ]
        ask firstInBuyQueue [
          die
        ]

        if orderBidID > orderAskID [
          set price currentOrderAsk
        ]
        if orderBidID < orderAskID [
          set price currentOrderBid
        ]

;        if(AuditTrail = true)[
;          set MatchID (MatchID + 1)
;          writetofile orderBidID "Bought" price orderQuantityBid traderBidType traderBidNum 1 MatchID orderHON1Bid orderHON2Bid
;          writetofile orderAskID "Sold" price orderQuantityBid traderAskType traderAskNum 2 MatchID orderHON1Ask orderHON2Ask
;        ]
        hatch-order_updates 1 [Order_Update orderBidID price "Bought" traderBidNum orderQuantityBid traderBid traderBidType]
        hatch-order_updates 1 [Order_Update orderAskID price "Sold"   traderAskNum orderQuantityBid traderAsk traderAskType]

        ask traderBid [
          set sharesOwned (sharesOwned + orderQuantityBid)
          set averageBoughtPrice ((averageBoughtPrice * totalBought + (price / 4) * orderQuantityBid) / (totalBought + orderQuantityBid))
          set totalBought (totalBought + orderQuantityBid)
        ]
        ask traderAsk [
          set sharesOwned (sharesOwned - orderQuantityBid)
          set averageSoldPrice ((averageSoldPrice * totalSold + (price / 4) * orderQuantityBid) / (totalSold + orderQuantityBid + 1))
          set totalSold (totalSold + orderQuantityBid)
        ]
        set volume (volume + orderQuantityBid)

        transactionOrder
      ]
    ]
  ]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;==============================================================================
;==============================================================================
;==============================================================================
;============ TRADER BEHAVIORAL SPECIFICATIONS ================================
;==============================================================================
;==============================================================================
;==============================================================================

;==============================================================================
;================= Order_Setup UTILITY FUNCTION ===============================
;==============================================================================
;//////////////////////////////////////////////////////////////////////////////
to Order_Setup [a b d f tdr tdrtype]

  ; a       OrderPrice
  ; b       OrderB/A
  ; d       OrderTraderID
  ; f       OrderQuantity
  ; tdr     TraderWho
  ; tdrtype TraderWhoType

  set orderNumber (orderNumber + 1)

  set OrderPrice a
  set OrderB/A b
  set OrderTraderID d
  set OrderTime ticks
  set OrderID orderNumber
  set OrderQuantity f
  set PriceOrder (OrderPrice * 100000000000) + OrderID
  set TraderWho tdr
  set TraderWhoType tdrtype
  set HON1 1
  set HON2 "-"

  let bora 0
  let tradernum 0
  let newCurrentBidPrice 0
  let newCurrentAskPrice 0

  ifelse b = "Buy" [
    set BuyOrderQueue lput self BuyOrderQueue
    set bora 1
  ] [
    set SellOrderQueue lput self SellOrderQueue
    set bora 2
  ]

  ask tdr [
    set openOrders lput myself openOrders
    set tradernum traderNumber
  ]
  set allOrders lput self allOrders

;  if(AuditTrail = true)[
;    writetofile OrderID OrderB/A OrderPrice OrderQuantity TraderWhoType tradernum bora "-" HON1 HON2
;  ]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to Order_Update [OID a b d f tdr tdrtype]

  set OrderPrice a
  set OrderB/A b
  set OrderTraderID d
  set OrderTime ticks
  set OrderID OID
  set OrderQuantity f
  set TraderWho tdr
  set TraderWhoType tdrtype

  set allOrders lput self allOrders

end
;code by Mark Flood
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report prop_allOrders [index factoid_name]

  ifelse (index < 0) or (index >= length allOrders) [
    report (word "Index out of range in prop_allOrders: " index)
  ] [
    let ord (item index allOrders)
    if (factoid_name = "OrderID")       [ report [OrderID]            of (ord) ]
    if (factoid_name = "OrderTime")     [ report [OrderTime]          of (ord) ]
    if (factoid_name = "OrderPrice")    [ report [OrderPrice]         of (ord) ]
    if (factoid_name = "OrderTraderID") [ report [OrderTraderID]      of (ord) ]
    if (factoid_name = "OrderQuantity") [ report [OrderQuantity]      of (ord) ]
    if (factoid_name = "OrderB/A")      [ report [OrderB/A]           of (ord) ]
    if (factoid_name = "TraderWho")     [ report [[who] of TraderWho] of (ord) ]
    if (factoid_name = "TraderWhoType") [ report [TraderWhoType]      of (ord) ]
    report (word "No property in prop_allOrders for factoid_name: " factoid_name)
  ]
end
;code by Mark Flood
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

;//////////////////////////////////////////////////////////////////////////////
to-report prop_list_orders [index factoid_name]

  ifelse (index < 0) or (index >= length list_orders) [
    report (word "Index out of range in prop_list_orders: " index)
  ] [
    let ord (item index list_orders)
    if (factoid_name = "OrderID")       [ report [OrderID]            of (ord) ]
    if (factoid_name = "OrderTime")     [ report [OrderTime]          of (ord) ]
    if (factoid_name = "OrderPrice")    [ report [OrderPrice]         of (ord) ]
    if (factoid_name = "OrderTraderID") [ report [OrderTraderID]      of (ord) ]
    if (factoid_name = "OrderQuantity") [ report [OrderQuantity]      of (ord) ]
    if (factoid_name = "OrderB/A")      [ report [OrderB/A]           of (ord) ]
    if (factoid_name = "TraderWho")     [ report [[who] of TraderWho] of (ord) ]
    if (factoid_name = "TraderWhoType") [ report [TraderWhoType]      of (ord) ]
    report (word "No property in prop_list_orders for factoid_name: " factoid_name)
  ]
end
;code by Mark Flood
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

;//////////////////////////////////////////////////////////////////////////////
to-report prop_list_traders [index factoid_ID]
  let FACT_TraderNumber 1
  let FACT_TypeOfTrader 2
  let FACT_SharesOwned  3

  ifelse (index < 0) or (index >= length list_traders) [
    report (word "Index out of range in prop_list_traders: " index)
  ] [
    let trd (item index list_traders)
    if (factoid_ID = FACT_TraderNumber) [ report [traderNumber] of (trd) ]
    if (factoid_ID = FACT_TypeOfTrader) [ report [typeOfTrader] of (trd) ]
    if (factoid_ID = FACT_SharesOwned)  [ report [sharesOwned]  of (trd) ]
    report (word "No property in prop_list_traders for factoid_ID: " factoid_ID)
  ]
end
;code by Mark Flood
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

;------------------------------------------------------------------------------


;==============================================================================
;============ market_maker_agent BEHAVIORAL SPECIFICATION =====================
;==============================================================================
;//////////////////////////////////////////////////////////////////////////////
to MktMkr_Setup
  set typeOfTrader "MarketMakers"
  set speed 1000
  set tradeSpeedAdjustment random 10
  set tradeStatus "Transact"
  set orderNumber 0
  set countticks 0
  set tradeAccount 0
  set sharesOwned 0
  set totalBought 1
  set totalSold 1
  set averageBoughtPrice 0
  set averageSoldPrice 0
  set movingAverageDIS 0
  set reversion 0
  set totalCanceled 0
  set buysell "B"
  set modify 0
  set openOrders []
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to MktMkr_distOrderBuy
  ;; Distribution of Order Quantity
  set tradeQuantity 5 * MktMkr_OrderSizeMult
  if(sharesOwned > (MktMkr_InvLimit / 5))[set tradeQuantity 4 * MktMkr_OrderSizeMult]
  if(sharesOwned > (MktMkr_InvLimit * 2 / 5))[set tradeQuantity 3 * MktMkr_OrderSizeMult]
  if(sharesOwned > (MktMkr_InvLimit * 3 / 5))[set tradeQuantity 2 * MktMkr_OrderSizeMult]
  if(sharesOwned > (MktMkr_InvLimit * 4 / 5))[set tradeQuantity 1 * MktMkr_OrderSizeMult]
  if(sharesOwned > (MktMkr_InvLimit))[set tradeQuantity 0 * MktMkr_OrderSizeMult]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to MktMkr_distOrderSell
  set tradeQuantity 5 * MktMkr_OrderSizeMult
  if(sharesOwned < (-1 * (MktMkr_InvLimit / 5)))[set tradeQuantity 4 * MktMkr_OrderSizeMult]
  if(sharesOwned < (-1 * (MktMkr_InvLimit * 2 / 5)))[set tradeQuantity 3 * MktMkr_OrderSizeMult]
  if(sharesOwned < (-1 * (MktMkr_InvLimit * 3 / 5)))[set tradeQuantity 2 * MktMkr_OrderSizeMult]
  if(sharesOwned < (-1 * (MktMkr_InvLimit * 4 / 5)))[set tradeQuantity 1 * MktMkr_OrderSizeMult]
  if(sharesOwned < (-1 * (MktMkr_InvLimit)))[set tradeQuantity 0 * MktMkr_OrderSizeMult]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to MktMkr_strategy
  let OrderCheckList table:make

  MktMkr_distOrderBuy

  table:put OrderCheckList 2 tradeQuantity
  table:put OrderCheckList 3 tradeQuantity
  table:put OrderCheckList 4 tradeQuantity
  table:put OrderCheckList 5 tradeQuantity
  table:put OrderCheckList 6 tradeQuantity
  table:put OrderCheckList 7 tradeQuantity
  table:put OrderCheckList 8 tradeQuantity

  MktMkr_distOrderSell

  table:put OrderCheckList -2 tradeQuantity
  table:put OrderCheckList -3 tradeQuantity
  table:put OrderCheckList -4 tradeQuantity
  table:put OrderCheckList -5 tradeQuantity
  table:put OrderCheckList -6 tradeQuantity
  table:put OrderCheckList -7 tradeQuantity
  table:put OrderCheckList -8 tradeQuantity

  foreach openorders [
    ask ?[
      ifelse OrderB/A = "Buy" [
        let OrderPriceDelta (price - OrderPrice + 1)

        ifelse (table:has-key? OrderCheckList OrderPriceDelta) [

          if (OrderQuantity != table:get OrderCheckList OrderPriceDelta) [
            set orderNumber (orderNumber + 1)
            set OrderQuantity table:get OrderCheckList OrderPriceDelta
            set PriceOrder (OrderPrice * 100000000000) + orderNumber
            set HON2 HON1
            set HON1 (HON1 + 1)

;            if(AuditTrail = true)[
;              writetofile OrderID "Modify" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;            ]
            hatch-order_updates 1 [Order_Update OrderID OrderPrice "Modify" tradernumber OrderQuantity TraderWho TraderWhoType]
          ]

          table:remove OrderCheckList OrderPriceDelta
        ] [
          let OrderCancel OrderQuantity
          ask TraderWho [
            set openorders remove ? openorders
            set totalCanceled (totalCanceled + OrderCancel)
          ]

;          if(AuditTrail = true)[
;            writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;          ]
          hatch-order_updates 1 [Order_Update OrderID OrderPrice "Cancel" tradernumber OrderQuantity TraderWho TraderWhoType]

          die
        ]
      ][
        let OrderPriceDelta (price - OrderPrice - 1)

        ifelse table:has-key? OrderCheckList OrderPriceDelta [

          if OrderQuantity != table:get OrderCheckList OrderPriceDelta [
            set orderNumber (orderNumber + 1)
            set OrderQuantity table:get OrderCheckList OrderPriceDelta
            set PriceOrder (OrderPrice * 100000000000) + orderNumber
            set HON2 HON1
            set HON1 (HON1 + 1)

;            if(AuditTrail = true)[
;              writetofile OrderID "Modify" OrderPrice OrderQuantity TraderWhoType tradernumber 2 "-" HON1 HON2
;            ]
            hatch-order_updates 1 [Order_Update OrderID OrderPrice "Modify" tradernumber OrderQuantity TraderWho TraderWhoType]
          ]

          table:remove OrderCheckList OrderPriceDelta
        ] [
          let OrderCancel OrderQuantity
          ask TraderWho [
            set openorders remove ? openorders
            set totalCanceled (totalCanceled + OrderCancel)
          ]

;          if(AuditTrail = true)[
;            writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 2 "-" HON1 HON2
;          ]
          hatch-order_updates 1 [Order_Update OrderID OrderPrice "Cancel" tradernumber OrderQuantity TraderWho TraderWhoType]

          die
        ]
      ]
    ]
  ]

  let i -10
  while [i < 11][
    let BuySellDecision "0"
    ifelse i > 0 [
      set BuySellDecision "Buy"
    ] [
      set BuySellDecision "Sell"
    ]

    if table:has-key? OrderCheckList i [
      ifelse BuySellDecision = "Buy" [
        hatch-orders 1 [Order_Setup (price - (i - 1)) BuySellDecision traderNumber (table:get OrderCheckList i) myself typeOfTrader]
      ] [
        hatch-orders 1 [Order_Setup (price - (i + 1)) BuySellDecision traderNumber (table:get OrderCheckList i) myself typeOfTrader]
      ]
    ]
    set i (i + 1)
  ]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report MktMkr_avgShares
;  ifelse((count turtles with [typeOfTrader = "MarketMakers"]) > 0) [
;    report precision (((sum [sharesOwned] of traders with [typeOfTrader = "MarketMakers"])) / (count traders with [typeOfTrader = "MarketMakers"]))  2
;  ] [
;    report 0
;  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report MktMkr_accountValue
;  ifelse((count turtles with [typeOfTrader = "MarketMakers"]) > 0) [
;    report precision ((sum [tradeAccount] of traders with [typeOfTrader = "MarketMakers"]) / (count traders with [typeOfTrader = "MarketMakers"])) 2
;  ] [
;    report 0
;  ]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
;------------------------------------------------------------------------------


;==============================================================================
;============ liquidity_demander_agent BEHAVIORAL SPECIFICATION ===============
;==============================================================================
;code by Mark Paddrik
;//////////////////////////////////////////////////////////////////////////////
to LiqDem_Setup
  set typeOfTrader "LiquidityDemander"
  set speed (random-poisson 300) + 1
  set tradeSpeedAdjustment (random 30) + 1
  set tradeStatus "Transact"
  set orderNumber 0
  set countticks 0
  set tradeAccount 0
  set sharesOwned 0
  set totalBought 1
  set totalSold 1
  set averageBoughtPrice 0
  set averageSoldPrice 0
  set totalCanceled 0
  set buysell "B"
  set modify 0
  set openOrders []
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to LiqDem_distOrder
  ;; Distribution of Order Quantity
  let randDraw random 100
  set tradeQuantity 1 * LiqDem_OrderSizeMult
  if(randDraw > 31)[set tradeQuantity 2 * LiqDem_OrderSizeMult]
  if(randDraw > 50)[set tradeQuantity 3 * LiqDem_OrderSizeMult]
  if(randDraw > 63)[set tradeQuantity 4 * LiqDem_OrderSizeMult]
  if(randDraw > 73)[set tradeQuantity 5 * LiqDem_OrderSizeMult]
  if(randDraw > 82)[set tradeQuantity 6 * LiqDem_OrderSizeMult]
  if(randDraw > 94)[set tradeQuantity 7 * LiqDem_OrderSizeMult]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to LiqDem_distPriceBuy
  ;Distribution of Price Selection
  let randDraw random 10000
  set tradePrice price - 10
  if(randDraw < 2800 and ticks > 5001)[set tradePrice price + 5]
  if(randDraw < 4400 and randDraw >= 2800)[set tradePrice price - 1 ]
  if(randDraw < 5600 and randDraw >= 4400)[set tradePrice price - 2 ]
  if(randDraw < 6500 and randDraw >= 5600)[set tradePrice price - 3 ]
  if(randDraw < 7200 and randDraw >= 6500)[set tradePrice price - 4 ]
  if(randDraw < 7800 and randDraw >= 7200)[set tradePrice price - 5 ]
  if(randDraw < 8400 and randDraw >= 7800)[set tradePrice price - 6 ]
  if(randDraw < 8800 and randDraw >= 8400)[set tradePrice price - 7 ]
  if(randDraw < 9300 and randDraw >= 8800)[set tradePrice price - 8 ]
  if(randDraw < 9600 and randDraw >= 9300)[set tradePrice price - 9 ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to LiqDem_distPriceSell
  let randDraw random 10000
  set tradePrice price + 10
  if(randDraw < 2800 and ticks > 5001)[set tradePrice price - 5 ]
  if(randDraw < 4400 and randDraw >= 2800)[set tradePrice price + 1 ]
  if(randDraw < 5600 and randDraw >= 4400)[set tradePrice price + 2 ]
  if(randDraw < 6500 and randDraw >= 5600)[set tradePrice price + 3 ]
  if(randDraw < 7200 and randDraw >= 6500)[set tradePrice price + 4 ]
  if(randDraw < 7800 and randDraw >= 7200)[set tradePrice price + 5 ]
  if(randDraw < 8400 and randDraw >= 7800)[set tradePrice price + 6 ]
  if(randDraw < 8800 and randDraw >= 8400)[set tradePrice price + 7 ]
  if(randDraw < 9300 and randDraw >= 8800)[set tradePrice price + 8 ]
  if(randDraw < 9600 and randDraw >= 9300)[set tradePrice price + 9 ]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to LiqDem_strategy
  let bern random 3

  if(bern = 1) [
    foreach openorders [
      ask ?[
;        if(AuditTrail = true) [
;          writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;        ]
        hatch-order_updates 1 [Order_Update OrderID OrderPrice "Cancel" tradernumber OrderQuantity myself TraderWhoType]
        die
      ]
    ]
    set openorders []
  ]

  if(timeseries = True and ticks > 5000) [
    if sum [sharesOwned] of traders with [typeOfTrader = "LiquidityDemander"] < timeseriesvalue [
       if (resethillclimbto50 = -1)[
         set LiqDem_ProbBuy 50
       ]
       set resethillclimbto50 1
       set LiqDem_ProbBuy (LiqDem_ProbBuy + (sqrt(100 - LiqDem_ProbBuy)) / 100)
    ]
    if sum [sharesOwned] of traders with [typeOfTrader = "LiquidityDemander"] > timeseriesvalue [
       if (resethillclimbto50 = 1)[
         set LiqDem_ProbBuy 50
       ]
       set resethillclimbto50 -1
       set LiqDem_ProbBuy (LiqDem_ProbBuy - (sqrt(abs(LiqDem_ProbBuy))) / 100)
    ]
  ]

  let randDraw random 10000
  ifelse randDraw < ((LiqDem_ProbBuy * 100) + 125) [
    set tradeStatus "Buy"
    LiqDem_distPriceBuy
    LiqDem_distOrder
  ] [
    set tradeStatus "Sell"
    LiqDem_distPriceSell
    LiqDem_distOrder
  ]

  hatch-orders 1 [Order_Setup tradePrice tradeStatus traderNumber tradeQuantity myself typeOfTrader]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report LiqDem_avgShares
  ifelse((count turtles with [typeOfTrader = "LiquidityDemander"]) > 0) [
    report precision (((sum [sharesOwned] of traders with [typeOfTrader = "LiquidityDemander"])) / (count traders with [typeOfTrader = "LiquidityDemander"]))  2
  ] [
    report 0
  ]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report LiqDem_accountValue
  ifelse((count turtles with [typeOfTrader = "LiquidityDemander"]) > 0) [
    report precision ((sum [tradeAccount] of traders with [typeOfTrader = "LiquidityDemander"]) / (count traders with [typeOfTrader = "LiquidityDemander"])) 2
  ] [
    report 0
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
;------------------------------------------------------------------------------


;==============================================================================
;============ liquidity_supplier_agent BEHAVIORAL SPECIFICATION ===============
;==============================================================================
;//////////////////////////////////////////////////////////////////////////////
to LiqSup_Setup
  set typeOfTrader "LiquiditySupplier"
  set speed (random-poisson LiqSup_ArrivalRate) + 1
  set tradeSpeedAdjustment (random 30) + 1
  set tradeStatus "Transact"
  set orderNumber 0
  set countticks 0
  set tradeAccount 0
  set sharesOwned 0
  set totalBought 1
  set totalSold 1
  set averageBoughtPrice 0
  set averageSoldPrice 0
  set totalCanceled 0
  set buysell "B"
  set modify 0
  set openOrders []
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to LiqSup_distOrderBuy
  ;; Distribution of Order Quantity
  let priceChange ((price / 4) - 100)

  let multipleSizePrice (precision ((-1 * priceChange) / LiqSup_PctPriceChange) 0) + 1

  if (multipleSizePrice <= 0) [set multipleSizePrice 1]

  let randDraw random 100
  set tradeQuantity 1 * LiqSup_OrderSizeMult * multipleSizePrice
  if(randDraw > 32)[set tradeQuantity 2 * LiqSup_OrderSizeMult * multipleSizePrice]
  if(randDraw > 50)[set tradeQuantity 3 * LiqSup_OrderSizeMult * multipleSizePrice]
  if(randDraw > 63)[set tradeQuantity 4 * LiqSup_OrderSizeMult * multipleSizePrice]
  if(randDraw > 73)[set tradeQuantity 5 * LiqSup_OrderSizeMult * multipleSizePrice]
  if(randDraw > 82)[set tradeQuantity 6 * LiqSup_OrderSizeMult * multipleSizePrice]
  if(randDraw > 94)[set tradeQuantity 7 * LiqSup_OrderSizeMult * multipleSizePrice]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to LiqSup_distOrderSell
  let priceChange ((price / 4) - 100)

  let multipleSizePrice (precision ((priceChange) / LiqSup_PctPriceChange) 0) + 1

  if (multipleSizePrice <= 0) [set multipleSizePrice 1]

  let randDraw random 100
  set tradeQuantity 1 * LiqSup_OrderSizeMult * multipleSizePrice
  if(randDraw > 32)[set tradeQuantity 2 * LiqSup_OrderSizeMult * multipleSizePrice]
  if(randDraw > 50)[set tradeQuantity 3 * LiqSup_OrderSizeMult * multipleSizePrice]
  if(randDraw > 63)[set tradeQuantity 4 * LiqSup_OrderSizeMult * multipleSizePrice]
  if(randDraw > 73)[set tradeQuantity 5 * LiqSup_OrderSizeMult * multipleSizePrice]
  if(randDraw > 82)[set tradeQuantity 6 * LiqSup_OrderSizeMult * multipleSizePrice]
  if(randDraw > 94)[set tradeQuantity 7 * LiqSup_OrderSizeMult * multipleSizePrice]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to LiqSup_distPriceBuy
  ;Distribution of Price Selection
  let randDraw random 1000
  set tradePrice price - 11
  if(randDraw < 40 and ticks > 5001)[set tradePrice price + 5 ]
  if(randDraw < 80 and randDraw >= 60)[set tradePrice price - 1 ]
  if(randDraw < 110 and randDraw >= 70)[set tradePrice price - 2 ]
  if(randDraw < 160 and randDraw >= 110)[set tradePrice price - 3 ]
  if(randDraw < 200 and randDraw >= 160)[set tradePrice price - 4 ]
  if(randDraw < 260 and randDraw >= 200)[set tradePrice price - 5 ]
  if(randDraw < 320 and randDraw >= 260)[set tradePrice price - 6 ]
  if(randDraw < 390 and randDraw >= 320)[set tradePrice price - 7 ]
  if(randDraw < 480 and randDraw >= 390)[set tradePrice price - 8 ]
  if(randDraw < 600 and randDraw >= 480)[set tradePrice price - 9 ]
  if(randDraw < 760 and randDraw >= 600)[set tradePrice price - 10 ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to LiqSup_distPriceSell
  let randDraw random 1000
  set tradePrice price + 11
  if(randDraw < 20 and ticks > 5001)[set tradePrice price - 5 ]
  if(randDraw < 40 and randDraw >= 20)[set tradePrice price + 1 ]
  if(randDraw < 70 and randDraw >= 40)[set tradePrice price + 2 ]
  if(randDraw < 120 and randDraw >= 70)[set tradePrice price + 3 ]
  if(randDraw < 160 and randDraw >= 120)[set tradePrice price + 4 ]
  if(randDraw < 220 and randDraw >= 160)[set tradePrice price + 5 ]
  if(randDraw < 280 and randDraw >= 220)[set tradePrice price + 6 ]
  if(randDraw < 350 and randDraw >= 280)[set tradePrice price + 7 ]
  if(randDraw < 440 and randDraw >= 350)[set tradePrice price + 8 ]
  if(randDraw < 560 and randDraw >= 440)[set tradePrice price + 9 ]
  if(randDraw < 720 and randDraw >= 560)[set tradePrice price + 10 ]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to LiqSup_strategy
  let bern random 3

  if(bern = 1) [
    foreach openorders [
      ask ?[
;        if(AuditTrail = true)[
;          writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;        ]
        hatch-order_updates 1 [Order_Update OrderID OrderPrice "Cancel" tradernumber OrderQuantity myself TraderWhoType]
        die
      ]
    ]
    set openorders []
  ]

  let randDraw random 10000
  ifelse randDraw < 5000 [
     set tradeStatus "Buy"
     LiqSup_distPriceBuy
     LiqSup_distOrderBuy
  ] [
     set tradeStatus "Sell"
     LiqSup_distPriceSell
     LiqSup_distOrderSell
  ]

  hatch-orders 1 [Order_Setup tradePrice tradeStatus traderNumber tradeQuantity myself typeOfTrader]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report LiqSup_avgShares
  ifelse((count turtles with [typeOfTrader = "LiquiditySupplier"]) > 0) [
    report precision (((sum [sharesOwned] of traders with [typeOfTrader = "LiquiditySupplier"])) / (count traders with [typeOfTrader = "LiquiditySupplier"]))  2
  ] [
    report 0
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report LiqSup_accountValue
  ifelse((count turtles with [typeOfTrader = "LiquiditySupplier"]) > 0) [
    report precision ((sum [tradeAccount] of traders with [typeOfTrader = "LiquiditySupplier"]) / (count traders with [typeOfTrader = "LiquiditySupplier"])) 2
  ] [
    report 0
  ]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

;------------------------------------------------------------------------------



;==============================================================================
;============ high_frequency_agent BEHAVIORAL SPECIFICATION ===================
;==============================================================================
;//////////////////////////////////////////////////////////////////////////////
to HftTdr_Setup
  set typeOfTrader "HighFrequency"
  set speed (1 + (random-poisson 3))
  set tradeSpeedAdjustment random 2
  set tradeStatus "Transact"
  set orderNumber 0
  set countticks 0
  set tradeAccount 0
  set sharesOwned 0
  set totalBought 0
  set totalSold 0
  set averageBoughtPrice 0
  set averageSoldPrice 0
  set movingAverageDIS 0
  set reversion 0
  set totalCanceled 0
  set buysell "B"
  set modify 0
  set openOrders []
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

;//////////////////////////////////////////////////////////////////////////////
to HftTdr_distOrder
  ;; Distribution of Order Quantity
  let randDraw random 100
  set tradeQuantity 1
  if(randDraw > 57)[set tradeQuantity 2 ]
  if(randDraw > 76)[set tradeQuantity 3 ]
  if(randDraw > 80)[set tradeQuantity 4 ]
  if(randDraw > 85)[set tradeQuantity 5 ]
  if(randDraw > 90)[set tradeQuantity 6 ]
  if(randDraw > 95)[set tradeQuantity 7 ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
; TODO: It appears this function is never called -- delete?
;to HftTdr_distPriceBuy
;  ;; Distribution of Price Selection
;  let randDraw random 100
;  set tradePrice price - 7
;  if(randDraw > 5)[set tradePrice price - 6 ]
;  if(randDraw > 20)[set tradePrice price - 5 ]
;  if(randDraw > 40)[set tradePrice price - 4 ]
;  if(randDraw > 55)[set tradePrice price - 3 ]
;  if(randDraw > 70)[set tradePrice price - 2 ]
;  if(randDraw > 85)[set tradePrice price - 1 ]
;  if(randDraw > 98 and ticks > 10005)[set tradePrice price + 5 ]
;end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
; TODO: It appears this function is never called -- delete?
;to HftTdr_distPriceSell
;  let randDraw random 100
;  set tradePrice price + 7
;  if(randDraw > 5)[set tradePrice price + 6 ]
;  if(randDraw > 20)[set tradePrice price + 5 ]
;  if(randDraw > 40)[set tradePrice price + 4 ]
;  if(randDraw > 55)[set tradePrice price + 3 ]
;  if(randDraw > 70)[set tradePrice price + 2 ]
;  if(randDraw > 85)[set tradePrice price + 1 ]
;  if(randDraw > 98 and ticks > 10005)[set tradePrice price - 5 ]
;end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to HftTdr_strategy
  foreach openorders [
    ask ?[
;      if(AuditTrail = true)[
;        writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;      ]
      hatch-order_updates 1 [Order_Update OrderID OrderPrice "Cancel" tradernumber OrderQuantity myself TraderWhoType]
      die
    ]
  ]

  set openorders []

  let numberOfBids length buyQueue
  let numberOfAsks length sellQueue
  let action "Neutral"

  ifelse (sharesOwned < 3  and sharesOwned > -3 and reversion = 0) [
    ifelse(abs(currentMA - (100 + (price / 5))) > 6 or movingAverageDIS = 1) [
      ifelse(abs(currentMA - (100 + (price / 5))) <= 2) [
        set movingAverageDIS  0
      ] [
        set movingAverageDIS  1
        ifelse(currentMA > (100 + (price / 5))) [
          set action "Buy"
          set tradePrice (currentBid + random 4 - 3 )
        ] [
          set action "Sell"
          set tradePrice (price - 1)
        ]
      ]
    ] [
      ifelse( random 100 < 30 and ( sharesOwned > 6 or sharesOwned < -6)) [
        ifelse (sharesOwned > 0) [
          set action "Sell"
          set tradePrice (currentAsk - random 4 + 3 )
        ] [
          set action "Buy"
          set tradePrice (currentBid + random 4 - 3)
        ]
      ] [
        ifelse(currentSQD >= currentBQD + random 21 - 10) [
          set action "Sell"
          set tradePrice (price - random 3 + 1)
        ] [
          set action "Buy"
          set tradePrice (price + random 3 - 1)
        ]
      ]
    ]
  ] [
    if (sharesOwned >= 3 or reversion = 1) [
      if(sharesOwned > 0) [
        set action "Sell"
        ifelse (random 100 < 60  or reversion = 1) [
          set reversion 1
          ifelse(sharesOwned > 6) [
            set tradePrice (price - random 4 + 3)
          ] [
            set reversion 0
            set tradePrice (price - random 4 + 3)
          ]
        ] [
          ifelse (random 100 < 10) [
            set tradePrice (currentAsk - random 4 + 3)
          ] [
            set tradePrice (currentAsk)
          ]
        ]
      ]
    ]
    if (sharesOwned <= -3 or reversion = 1) [
      if(sharesOwned < 0) [
        set action "Buy"
        ifelse (random 100 < 60  or reversion = 1) [
          set reversion 1
          ifelse(sharesOwned < -6) [
            set tradePrice (price + random 4 - 3)
          ] [
            set reversion 0
            set tradePrice (price + random 4 - 3)
          ]
        ] [
          ifelse (random 100 < 10) [
            set tradePrice (currentBid + random 4 - 3)
          ] [
            set tradePrice (currentBid)
          ]
        ]
      ]
    ]
  ]

  if (ticks < 5010) [
    if (action = "Buy") [set tradePrice price - 1 - random 4]
    if (action = "Sell") [set tradePrice price + 1 + random 4]
  ]

  set tradeStatus action
  HftTdr_distOrder
  hatch-orders 1 [Order_Setup tradePrice tradeStatus traderNumber tradeQuantity myself typeOfTrader]

end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report HftTdr_avgShares
  ifelse((count turtles with [typeOfTrader = "HighFrequency"]) > 0) [
    report precision (((sum [sharesOwned] of traders with [typeOfTrader = "HighFrequency"])) / (count traders with [typeOfTrader = "HighFrequency"]))  2
  ] [
    report 0
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report HftTdr_accountValue
  ifelse((count turtles with [typeOfTrader = "HighFrequency"]) > 0) [
    report precision ((sum [tradeAccount] of traders with [typeOfTrader = "HighFrequency"]) / (count traders with [typeOfTrader = "HighFrequency"])) 2
  ] [
    report 0
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
;------------------------------------------------------------------------------


;==============================================================================
;============ opportunistic_agent BEHAVIORAL SPECIFICATION ====================
;==============================================================================
;//////////////////////////////////////////////////////////////////////////////
to OppTdr_Setup
  set typeOfTrader "OpportunisticTraders"
  set speed (random-poisson 300)
  set tradeSpeedAdjustment random 200
  set tradeStatus "Transact"
  set orderNumber 0
  set countticks 0
  set tradeAccount 0
  set sharesOwned 0
  set totalBought 0
  set totalSold 0
  set averageBoughtPrice 0
  set averageSoldPrice 0
  set color white
  set totalCanceled 0
  set buysell "B"
  set modify 0
  set openOrders []
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
; TODO: It appears this function is never called -- delete?
;to OppTdr_distOrder
;  ;; Distribution of Order Quantity
;  let randDraw random 100
;  set tradeQuantity 1
;  if(randDraw > 66)[set tradeQuantity 2 ]
;  if(randDraw > 82)[set tradeQuantity 3 ]
;  if(randDraw > 87)[set tradeQuantity 4 ]
;  if(randDraw > 91)[set tradeQuantity 5 ]
;  if(randDraw > 94)[set tradeQuantity 6 ]
;  if(randDraw > 97)[set tradeQuantity 7 ]
;end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
; TODO: It appears this function is never called -- delete?
;to OppTdr_distPriceBuy
;  ;Distribution of Price Selection
;  let randDraw random 100
;  set tradePrice price - 10
;  if(randDraw < 36 and ticks > 10005)[set tradePrice price + 5 ]
;  if(randDraw > 35)[set tradePrice price - 1 ]
;  if(randDraw > 55)[set tradePrice price - 2 ]
;  if(randDraw > 60)[set tradePrice price - 3 ]
;  if(randDraw > 65)[set tradePrice price - 4 ]
;  if(randDraw > 70)[set tradePrice price - 5 ]
;  if(randDraw > 75)[set tradePrice price - 6 ]
;  if(randDraw > 80)[set tradePrice price - 7 ]
;  if(randDraw > 85)[set tradePrice price - 8 ]
;  if(randDraw > 90 and randDraw < 96)[set tradePrice price - 9 ]
;end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
; TODO: It appears this function is never called -- delete?
;to OppTdr_distPriceSell
;  let randDraw random 100
;  set tradePrice price + 10
;  if(randDraw < 36 and ticks > 10005)[set tradePrice price - 5 ]
;  if(randDraw > 35)[set tradePrice price + 1 ]
;  if(randDraw > 55)[set tradePrice price + 2 ]
;  if(randDraw > 60)[set tradePrice price + 3 ]
;  if(randDraw > 65)[set tradePrice price + 4 ]
;  if(randDraw > 70)[set tradePrice price + 5 ]
;  if(randDraw > 75)[set tradePrice price + 6 ]
;  if(randDraw > 80)[set tradePrice price + 7 ]
;  if(randDraw > 85)[set tradePrice price + 8 ]
;  if(randDraw > 90 and randDraw < 96)[set tradePrice price + 9 ]
;end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to OppTdr_strategy
  ;Automated Opportunistic Trader

  foreach openorders [
    ask ?[
;      if(AuditTrail = true)[
;        writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;      ]
      hatch-order_updates 1 [Order_Update OrderID OrderPrice "Cancel" tradernumber OrderQuantity myself TraderWhoType]
      die
    ]
  ]

  set openorders []

  let randNum random 100
  set tradePrice price
  let action "Neutral"

  if (randNum < 100)[
    let numberOfBids (length buyQueue)  ;since we only use length this was needed to make sure there was an accurate count
    let numberOfAsks length sellQueue
    let difference (numberOfBids - numberOfAsks)

    ifelse (sharesOwned < 1 and sharesOwned > -1 and reversion != 1) [
      ifelse(abs(currentMA - (100 + (price / 4))) > 10 or movingAverageDIS = 1) [
        ifelse(abs(currentMA - (100 + (price / 4))) <= 2) [
          set movingAverageDIS  0
        ] [
          set movingAverageDIS  1
          ifelse(currentMA > (100 + (price / 4))) [
            set action "Buy"
            set tradePrice (currentBid + 1)
          ] [
            set action "Sell"
            set tradePrice (price - 1)
          ]
        ]
      ] [
        ifelse( random 100 < 25 and ( sharesOwned > 1 or sharesOwned < -1)) [
          ifelse (sharesOwned > 0) [
            set action "Sell"
            set tradePrice (currentAsk )
          ] [
            set action "Buy"
            set tradePrice (currentBid )
          ]
        ] [
          ifelse ( random 100 < 50) [
            ifelse (numberOfAsks >= numberOfBids) [
              set action "Sell"
              set tradePrice (currentAsk - 2)
            ] [
              set action "Buy"
              set tradePrice (currentBid + 2)
            ]
          ] [
            ifelse (numberOfAsks >= numberOfBids) [
              set action "Sell"
              set tradePrice (currentAsk )
            ] [
              set action "Buy"
              set tradePrice (currentBid)
            ]
          ]
        ]
      ]
    ] [
      ifelse (sharesOwned > 0) [
        set action "Sell"
        ifelse (random 100 < 10  or reversion = 1) [
          set reversion 1
          ifelse(sharesOwned > 2) [
            set tradePrice (currentAsk - 2)
          ] [
            set reversion 0
            set tradePrice (currentAsk - 2)
          ]
        ] [
          ifelse (random 100 < 90) [
            set tradePrice (currentAsk - 2)
          ] [
            set tradePrice (currentAsk )
          ]
        ]
      ] [
        set action "Buy"
        ifelse (random 100 < 10  or reversion = 1) [
          set reversion 1
          ifelse(sharesOwned < -2) [
            set tradePrice (currentBid + 2)
          ] [
            set reversion 0
            set tradePrice (currentBid + 2)
          ]
        ] [
          ifelse (random 100 < 90) [
            set tradePrice (currentBid + 2)
          ] [
            set tradePrice (currentBid )
          ]
        ]
      ]
    ]
    set tradeQuantity int(1)
    set tradeStatus action
  ]

  if(randNum < 50) [
  ifelse (sharesOwned < 2 and sharesOwned > -2 and reversion != 1) [
    ifelse(abs(currentMA - (100 + (price / 4))) > 10 or movingAverageDIS = 1) [
      ifelse(abs(currentMA - (100 + (price / 4))) <= 2) [
        set movingAverageDIS  0
      ] [
        set movingAverageDIS  1
        ifelse(currentMA > (100 + (price / 4))) [
          set action "Buy"
          set tradePrice (currentBid + 1)
       ] [
          set action "Sell"
          set tradePrice (price - 1)
       ]
     ]
   ] [
     ifelse( random 100 < 25 and ( sharesOwned > 2 or sharesOwned < -2)) [
       ifelse (sharesOwned > 0) [
         set action "Sell"
         set tradePrice (currentAsk )
       ] [
         set action "Buy"
         set tradePrice (currentBid )
       ]
     ] [
       ifelse ( random 100 < 50) [
          ifelse (currentSQD >= currentBQD and currentSQD <= currentBQD + 15) [
            set action "Sell"
            set tradePrice (currentAsk - 2)
          ] [
            set action "Buy"
            set tradePrice (currentBid + 2)
          ]
        ] [
          ifelse (currentSQD >= currentBQD and currentSQD <= currentBQD + 15) [
            set action "Sell"
            set tradePrice (currentAsk )
          ] [
            set action "Buy"
            set tradePrice (currentBid)
          ]
        ]
      ]
    ]
  ] [
    ifelse (sharesOwned > 0) [
      set action "Sell"
      ifelse (random 100 < 10  or reversion = 1) [
        set reversion 1
        ifelse(sharesOwned > 2) [
          set tradePrice (currentAsk - 2)
        ] [
          set reversion 0
          set tradePrice (currentAsk - 2)
        ]
      ] [
        ifelse (random 100 < 50) [
          set tradePrice (currentAsk - 2)
        ] [
          set tradePrice (currentAsk )
        ]
      ]
    ] [
      ifelse( currentSQD >= currentBQD + 30) [
      set action "Buy"
      ifelse (random 100 < 10  or reversion = 1) [
        set reversion 1
        ifelse(sharesOwned < -2) [
          set tradePrice (currentBid + 2)
        ] [
          set reversion 0
          set tradePrice (currentBid + 2)
        ]
      ] [
        ifelse (random 100 < 50) [
          set tradePrice (currentBid + 2)
        ] [
          set tradePrice (currentBid )
        ]
      ]
    ] [
      set tradePrice (currentBid + 2)
      set action "Sell" ]
    ]
  ]

  if(sharesOwned < -4) [
    set action "Buy"
    set tradePrice (price + random 4 - 2)
  ]
  if(sharesOwned > 4) [
    set action "Sell"
    set tradePrice (price - random 4 + 3)
  ]

;  if (ticks < 5010)[
;    if (action = "Buy")[set tradePrice price - 1 - random 4]
;    if (action = "Sell")[set tradePrice price + 1 + random 4]
;  ]
   set tradeStatus action
  ]

  hatch-orders 1 [Order_Setup tradePrice tradeStatus traderNumber tradeQuantity myself typeOfTrader]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report OppTdr_avgShares
  ifelse((count turtles with [typeOfTrader = "OpportunisticTraders"]) > 0) [
    report precision (((sum [sharesOwned] of traders with [typeOfTrader = "OpportunisticTraders"])) / (count traders with [typeOfTrader = "OpportunisticTraders"]))  2
  ] [
    report 0
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report OppTdr_accountValue
  ifelse((count turtles with [typeOfTrader = "OpportunisticTraders"]) > 0) [
    report precision ((sum [tradeAccount] of traders with [typeOfTrader = "OpportunisticTraders"]) / (count traders with [typeOfTrader = "OpportunisticTraders"])) 2
  ] [
    report 0
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
;------------------------------------------------------------------------------


;==============================================================================
;============ absolutetrader BEHAVIORAL SPECIFICATION =========================
;==============================================================================
;Author: Isaac Wright
;//////////////////////////////////////////////////////////////////////////////
to AbsTdr_Setup
  set typeOfTrader "absolutetrader"
  set speed (random-poisson 200) + 1
  set tradeSpeedAdjustment (random 30) + 1
  set tradeStatus "Transact"
  set orderNumber 0
  set countticks 0
  set tradeAccount 0
  set sharesOwned 0
  set totalBought 1
  set totalSold 1
  set averageBoughtPrice 0
  set averageSoldPrice 0
  set totalCanceled 0
  set buysell "B"
  set modify 0
  set openOrders []
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to AbsTdr_distOrder
  ; Distribution of Order Quantity
  let randDraw random 100
  set tradeQuantity 1
  if(randDraw > 66)[set tradeQuantity 2 ]
  if(randDraw > 82)[set tradeQuantity 3 ]
  if(randDraw > 87)[set tradeQuantity 4 ]
  if(randDraw > 91)[set tradeQuantity 5 ]
  if(randDraw > 94)[set tradeQuantity 6 ]
  if(randDraw > 97)[set tradeQuantity 7 ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to AbsTdr_strategy

  foreach openorders [
    ask ?[
;      TODO: ##EXTERNAL_IO##
;      if(AuditTrail = true)[
;        writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;      ]
      hatch-order_updates 1 [Order_Update OrderID OrderPrice "Cancel" tradernumber OrderQuantity myself TraderWhoType]
      die
    ]
  ]

  set openorders []

  let randDraw random 100
  ifelse (randDraw <  50 ) [
     set tradeStatus "Buy"
     set tradePrice 396
     AbsTdr_distOrder
  ] [
     set tradeStatus "Sell"
     set tradePrice 404
     AbsTdr_distOrder
  ]

  hatch-orders 1 [Order_Setup tradePrice tradeStatus traderNumber tradeQuantity myself typeOfTrader]
end
;Author: Isaac Wright
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report AbsTdr_avgShares
  ifelse((count turtles with [typeOfTrader = "absolutetrader"]) > 0) [
    report precision (((sum [sharesOwned] of traders with [typeOfTrader = "absolutetrader"])) / (count traders with [typeOfTrader = "absolutetrader"]))  2
  ] [
    report 0
  ]
end
;code by Isaac
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report AbsTdr_accountValue
  ifelse((count turtles with [typeOfTrader = "absolutetrader"]) > 0) [
    report precision ((sum [tradeAccount] of traders with [typeOfTrader = "absolutetrader"]) / (count traders with [typeOfTrader = "absolutetrader"])) 2
  ] [
    report 0
  ]
end
;code by Isaac
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
;------------------------------------------------------------------------------


;==============================================================================
;============ ratiotrader BEHAVIORAL SPECIFICATION ============================
;==============================================================================
;Author: Isaac Wright
;//////////////////////////////////////////////////////////////////////////////
to RatTdr_Setup
  set typeOfTrader "ratiotrader"
  set speed 10
  set tradeSpeedAdjustment 0
  set tradeStatus "Transact"
  set orderNumber 0
  set countticks 0
  set tradeAccount 0
  set sharesOwned 0
  set totalBought 1
  set totalSold 1
  set averageBoughtPrice 0
  set averageSoldPrice 0
  set totalCanceled 0
  set buysell "B"
  set modify 0
  set openOrders []
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to RatTdr_distOrder
  let randDraw random 100
  set tradeQuantity 4
  if(randDraw > 66)[set tradeQuantity 5 ]
  if(randDraw > 82)[set tradeQuantity 6 ]
  if(randDraw > 87)[set tradeQuantity 7 ]
  if(randDraw > 91)[set tradeQuantity 8 ]
  if(randDraw > 94)[set tradeQuantity 9 ]
  if(randDraw > 97)[set tradeQuantity 10 ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to RatTdr_strategy
  foreach openorders [
    ask ?[
;      if(AuditTrail = true) [
;        writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;      ]
      hatch-order_updates 1 [Order_Update OrderID OrderPrice "Cancel" tradernumber OrderQuantity myself TraderWhoType]
      die
    ]
  ]
  set openorders []

  if( length [OrderQuantity] of orders > 0 ) [

    ; Weight for the buy side
    let t 0
    let y 0
    let weightbuy 0
    while [ (t + 1)  <= (length (sort-on [(- PriceOrder)] orders with [OrderB/A = "Buy"] )) ] [
      set weightbuy ( weightbuy + (1 - p_weight) * ((p_weight)^(y)) * ( [OrderQuantity] of item t (sort-on [(- PriceOrder)] orders with [OrderB/A = "Buy"] ) ) )
      if (  (t + 1) < (length (sort-on [(- PriceOrder)] orders with [OrderB/A = "Buy"] ))) [
        if ( [OrderPrice] of item t (sort-on [(- PriceOrder)] orders with [OrderB/A = "Buy"] ) != [OrderPrice] of item (t + 1) (sort-on [(- PriceOrder)] orders with [OrderB/A = "Buy"] )) [
          set y (y + 1)
        ]
      ]
      set t (t + 1)
    ]

    ; Weight for the sell side
    let k 0
    let ky 0
    let weightsell 0
    while [ (k + 1) <= (length (sort-on [(PriceOrder)] orders with [OrderB/A = "Sell"] )) ] [
      set weightsell ( weightsell + (1 - p_weight) * ((p_weight)^(ky)) * ( [OrderQuantity] of item k (sort-on [( PriceOrder)] orders with [OrderB/A = "Sell"] ) ) )
      if(  (k + 1)  < (length (sort-on [(PriceOrder)] orders with [OrderB/A = "Sell"] )) ) [
        if ( [OrderPrice] of item k (sort-on [( PriceOrder)] orders with [OrderB/A = "Sell"] ) != [OrderPrice] of item (k + 1) (sort-on [(PriceOrder)] orders with [OrderB/A = "Sell"] )) [
          set ky (ky + 1)
        ]
      ]
      set k (k + 1)
    ]
    ;############### End Setup for weighting system

    if (sum [sharesOwned] of traders with [typeOfTrader = "ratiotrader"] < RatTdr_InvRatio) [
      if ( weightbuy / (weightsell + 1) > RatTdr_ImbalRatio ) [
        set tradeStatus "Buy"
        set tradePrice price + 2
        RatTdr_distOrder
        hatch-orders 1 [Order_Setup tradePrice tradeStatus traderNumber tradeQuantity myself typeOfTrader]
      ]
    ]

    if (sum [sharesOwned] of traders with [typeOfTrader = "ratiotrader"] > -1 * RatTdr_InvRatio) [
      if ( weightsell / (weightbuy + 1) > RatTdr_ImbalRatio ) [
        set tradeStatus "Sell"
        set tradePrice price - 2
        RatTdr_distOrder
        hatch-orders 1 [Order_Setup tradePrice tradeStatus traderNumber tradeQuantity myself typeOfTrader]
      ]
    ]
  ]

end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
;Author: Isaac Wright
to-report RatTdr_avgShares
  ifelse((count turtles with [typeOfTrader = "ratiotrader"]) > 0) [
    report precision (((sum [sharesOwned] of traders with [typeOfTrader = "ratiotrader"])) / (count traders with [typeOfTrader = "ratiotrader"]))  2
  ] [
    report 0
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
;------------------------------------------------------------------------------


;==============================================================================
;============ forced_sale_agent BEHAVIORAL SPECIFICATION ======================
;==============================================================================
;//////////////////////////////////////////////////////////////////////////////
to FrcSal_Setup
  set typeOfTrader "ForcedSale"
  set speed (random-poisson 5)
  set tradeSpeedAdjustment 1
  set tradeStatus "Cancel"
  set orderNumber 0
  set countticks 0
  set tradeAccount 0
  set sharesOwned 0
  set totalBought 1
  set totalSold 1
  set averageBoughtPrice 0
  set averageSoldPrice 0
  set totalCanceled 0
  set buysell "B"
  set modify 0
  set openOrders []
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to FrcSal_strategy
  foreach openorders [
    ask ?[
;      if(AuditTrail = true)[
;        writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;      ]
      hatch-order_updates 1 [Order_Update OrderID OrderPrice "Cancel" tradernumber OrderQuantity myself TraderWhoType]
      die
    ]
  ]

  set openorders []

  set tradeStatus "Sell"
  set tradePrice price - 5
  set tradeQuantity round ( (FrcSal_QuantSale + sharesOwned) / ((FrcSal_PerEndExec - ticks) / 6))

  hatch-orders 1 [Order_Setup tradePrice tradeStatus traderNumber tradeQuantity myself typeOfTrader]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report FrcSal_avgShares
  ifelse((count turtles with [typeOfTrader = "LiquiditySupplier"]) > 0) [
    report precision (((sum [sharesOwned] of traders with [typeOfTrader = "ForcedSale"])) / (count traders with [typeOfTrader = "ForcedSale"])) 2
  ] [
    report 0
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report FrcSal_accountValue
  ifelse((count turtles with [typeOfTrader = "LiquiditySupplier"]) > 0) [
    report precision ((sum [tradeAccount] of traders with [typeOfTrader = "ForcedSale"]) / (count traders with [typeOfTrader = "ForcedSale"])) 2
  ] [
    report 0
  ]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
;------------------------------------------------------------------------------


;==============================================================================
;============ spoofer BEHAVIORAL SPECIFICATION ================================
;==============================================================================
;Author: Isaac Wright
;//////////////////////////////////////////////////////////////////////////////
to SpfTdr_Setup
  set typeOfTrader "spoofer"
  set speed 1000
  set tradeSpeedAdjustment random 10
  set tradeStatus "Transact"
  set orderNumber 0
  set countticks 0
  set tradeAccount 0
  set sharesOwned 0
  set totalBought 1
  set totalSold 1
  set averageBoughtPrice 0
  set averageSoldPrice 0
  set movingAverageDIS 0
  set reversion 0
  set totalCanceled 0
  set buysell "B"
  set modify 0
  set openOrders []
  set pattern "abuy"
  set direct 1
  set move 100
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to SpfTdr_strategy

  ; ///////// Set up weighting system
  ; Weight for the buy side
  let t 0
  let y 0
  let weightbuy 0
  while [ (t + 1 )  <= (length (sort-on [(- PriceOrder)] orders with [OrderB/A = "Buy"] )) ]  [
    set weightbuy ( weightbuy + (1 - p_weight) * ((p_weight)^(y)) * ( [OrderQuantity] of item t (sort-on [(- PriceOrder)] orders with [OrderB/A = "Buy"] ) ) )
    if (  (t + 1) < (length (sort-on [(- PriceOrder)] orders with [OrderB/A = "Buy"] ))) [
      if ( [OrderPrice] of item t (sort-on [(- PriceOrder)] orders with [OrderB/A = "Buy"] ) != [OrderPrice] of item (t + 1) (sort-on [(- PriceOrder)] orders with [OrderB/A = "Buy"] )) [
        set y (y + 1)
      ]
    ]
    set t (t + 1)
  ]

  ; Weight for the sell side
  let k 0
  let ky 0
  let weightsell 0
  while [ ( k + 1 ) <= (length (sort-on [( PriceOrder)] orders with [OrderB/A = "Sell"] )) ] [
    set weightsell ( weightsell + (1 - p_weight) * ((p_weight)^(ky)) * ( [OrderQuantity] of item k (sort-on [( PriceOrder)] orders with [OrderB/A = "Sell"] ) ) )
    if(  (k + 1)  < (length (sort-on [(PriceOrder)] orders with [OrderB/A = "Sell"] )) ) [
      if ( [OrderPrice] of item k (sort-on [( PriceOrder)] orders with [OrderB/A = "Sell"] ) != [OrderPrice] of item (k + 1) (sort-on [(PriceOrder)] orders with [OrderB/A = "Sell"] )) [
        set ky (ky + 1)
      ]
    ]
    set k (k + 1)
  ]
  ; ^^^^^^^^^ End setup for weighting system

  if ( ( ( weightbuy  ) / ( weightsell + 1) ) >= 1 - SpfTdr_BalDistance and ( ( weightbuy  ) / ( weightsell + 1) ) <= 1 + SpfTdr_BalDistance ) [
    ;;;;;;;;;;;; Buy side spoof
    if (pattern = "abuy" and direct = 1) [
      let OrderCheckList table:make

      table:put OrderCheckList 4 50
      table:put OrderCheckList 5 50
      table:put OrderCheckList 6 50
      table:put OrderCheckList 7 50
      table:put OrderCheckList 8 50

      table:put OrderCheckList -2 5
      ;table:put OrderCheckList -3 5

      let i -10
      while [i < 11][
        let BuySellDecision "0"
        ifelse i > 0 [
          set BuySellDecision "Buy"
        ] [
          set BuySellDecision "Sell"
        ]

        if table:has-key? OrderCheckList i [
          ifelse BuySellDecision = "Buy" [
            hatch-orders 1 [Order_Setup (price - (i - 1)) BuySellDecision traderNumber (table:get OrderCheckList i) myself typeOfTrader]
          ] [
            hatch-orders 1 [Order_Setup (price - (i + 1)) BuySellDecision traderNumber (table:get OrderCheckList i) myself typeOfTrader]
          ]
        ]
        set i (i + 1)
      ]
      set tradeStatus "neutral"
      set pattern "abuyafter"
    ]
  ]

  ;After an overloading buy side and small sell side, cancel the buy side and just leave sell side
  if( pattern = "abuyafter" and tradeStatus = "Transact" and direct = 1 ) [

    foreach openorders [
      ask ?[
;       if(AuditTrail = true)[
;         writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;       ]
        hatch-order_updates 1 [Order_Update OrderID OrderPrice "Cancel" tradernumber OrderQuantity myself TraderWhoType]
        die
      ]
    ]

    set openorders []

    let OrderCheckList table:make

    table:put OrderCheckList 4 0
    table:put OrderCheckList 5 0
    table:put OrderCheckList 6 0
    table:put OrderCheckList 7 0
    table:put OrderCheckList 8 0

    table:put OrderCheckList -2 5
    ;table:put OrderCheckList -3 5

    let i -10
    while [i < 11][
      let BuySellDecision "0"
      ifelse i > 0 [
        set BuySellDecision "Buy"
      ] [
        set BuySellDecision "Sell"
      ]
      if table:has-key? OrderCheckList i [
        ifelse BuySellDecision = "Buy" [
          hatch-orders 1 [Order_Setup (price - (i - 1)) BuySellDecision traderNumber (table:get OrderCheckList i) myself typeOfTrader]
        ] [
          hatch-orders 1 [Order_Setup (price - (i + 1)) BuySellDecision traderNumber (table:get OrderCheckList i) myself typeOfTrader]
        ]
      ]
      set i (i + 1)
    ]

    set tradeStatus "neutral"
    set pattern "abuycancel"
  ]

  ;if the order does not excute, cancel and start over
  if ( pattern = "abuycancel" and tradeStatus = "Transact" and direct = 1) [
    foreach openorders [
      ask ?[
;        if(AuditTrail = true)[
;          writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;        ]
      hatch-order_updates 1 [Order_Update OrderID OrderPrice "Cancel" tradernumber OrderQuantity myself TraderWhoType]
      die
      ]
    ]

    set openorders []
    set tradeStatus "neutral"
    set direct 0
    if( direct = 0) [
      set pattern "asell"
    ]
  ]

  ;;;;;;;;;;;; Sell Side Spoof
  if( pattern = "asell" and direct = 0 ) [
    let OrderCheckList table:make

    table:put OrderCheckList 2 5
    ;table:put OrderCheckList 3 5

    table:put OrderCheckList -4 50
    table:put OrderCheckList -5 50
    table:put OrderCheckList -6 50
    table:put OrderCheckList -7 50
    table:put OrderCheckList -8 50

    let i -10
    while [i < 11] [
      let BuySellDecision "0"
      ifelse i > 0 [
        set BuySellDecision "Buy"
      ] [
        set BuySellDecision "Sell"
      ]

      if table:has-key? OrderCheckList i [
        ifelse BuySellDecision = "Buy" [
          hatch-orders 1 [Order_Setup (price - (i - 1)) BuySellDecision traderNumber (table:get OrderCheckList i) myself typeOfTrader]
        ] [
          hatch-orders 1 [Order_Setup (price - (i + 1)) BuySellDecision traderNumber (table:get OrderCheckList i) myself typeOfTrader]
        ]
      ]
      set i (i + 1)
    ]
    set tradeStatus "neutral"
    set pattern "asellafter"
  ]

  ;After an overloading buy side and small sell side, cancel the buy side and just leave sell side
  if( pattern = "asellafter" and tradeStatus = "Transact" and direct = 0 ) [
    foreach openorders [
      ask ?[
;        if(AuditTrail = true)[
;          writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;        ]
        hatch-order_updates 1 [Order_Update OrderID OrderPrice "Cancel" tradernumber OrderQuantity myself TraderWhoType]
        die
      ]
    ]

    set openorders []

    let OrderCheckList table:make

    table:put OrderCheckList 2 5
   ;table:put OrderCheckList 3 5

    table:put OrderCheckList -4 0
    table:put OrderCheckList -5 0
    table:put OrderCheckList -6 0
    table:put OrderCheckList -7 0
    table:put OrderCheckList -8 0

    let i -10
    while [i < 11] [
      let BuySellDecision "0"
      ifelse i > 0 [
        set BuySellDecision "Buy"
      ] [
        set BuySellDecision "Sell"
      ]

      if table:has-key? OrderCheckList i [
        ifelse BuySellDecision = "Buy" [
          hatch-orders 1 [Order_Setup (price - (i - 1)) BuySellDecision traderNumber (table:get OrderCheckList i) myself typeOfTrader]
        ] [
          hatch-orders 1 [Order_Setup (price - (i + 1)) BuySellDecision traderNumber (table:get OrderCheckList i) myself typeOfTrader]
        ]
      ]
      set i (i + 1)
    ]

    set tradeStatus "neutral"
    set pattern "asellcancel"
  ]

  ;if the order does not excute, cancel and start over
  if ( pattern = "asellcancel" and tradeStatus = "Transact" and direct = 0) [
    foreach openorders [
      ask ?[
;        if(AuditTrail = true)[
;          writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;        ]
        hatch-order_updates 1 [Order_Update OrderID OrderPrice "Cancel" tradernumber OrderQuantity myself TraderWhoType]
        die
      ]
    ]

    set openorders []
    set tradeStatus "neutral"
    set direct 1
    if( direct = 1) [
     set pattern "abuy"
    ]
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report SpfTdr_avgShares
  ifelse((count turtles with [typeOfTrader = "spoofer"]) > 0) [
    report precision (((sum [sharesOwned] of traders with [typeOfTrader = "spoofer"])) / (count traders with [typeOfTrader = "spoofer"]))  2
  ] [
    report 0
  ]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report SpfTdr_accountValue
  ifelse((count turtles with [typeOfTrader = "spoofer"]) > 0) [
    report precision ((sum [tradeAccount] of traders with [typeOfTrader = "spoofer"]) / (count traders with [typeOfTrader = "spoofer"])) 2
  ] [
    report 0
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^



;==============================================================================
;==============================================================================
;==============================================================================
;============= GRAPHICAL USER INTERFACE LAYOUT ================================
;==============================================================================
;==============================================================================
;==============================================================================

;------------------------------------------------------------------------------
@#$#@#$#@
GRAPHICS-WINDOW
210
10
649
470
16
16
13.0
1
10
1
1
1
0
1
1
1
-16
16
-16
16
0
0
1
ticks
30.0

BUTTON
15
15
135
48
Setup Model
setup
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

BUTTON
140
15
240
48
NIL
go
T
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

TEXTBOX
15
955
165
975
Market Maker
16
0.0
1

SLIDER
175
945
365
978
#_MktMkr
#_MktMkr
0
10
5
1
1
NIL
HORIZONTAL

SLIDER
857
945
1090
978
MktMkr_OrderSizeMult
MktMkr_OrderSizeMult
1
5
1
1
1
NIL
HORIZONTAL

SLIDER
399
945
619
978
MktMkr_TradeLength
MktMkr_TradeLength
0
60
30
10
1
NIL
HORIZONTAL

SLIDER
626
945
844
978
MktMkr_ArrivalRate
MktMkr_ArrivalRate
0
120
105
5
1
NIL
HORIZONTAL

SLIDER
1130
945
1355
978
MktMkr_InvLimit
MktMkr_InvLimit
5
100
100
5
1
NIL
HORIZONTAL

TEXTBOX
15
820
175
840
Liquidity Demander
16
0.0
1

SLIDER
175
815
365
848
#_LiqDem
#_LiqDem
0
250
100
1
1
NIL
HORIZONTAL

SLIDER
856
814
1089
847
LiqDem_OrderSizeMult
LiqDem_OrderSizeMult
1
10
10
1
1
NIL
HORIZONTAL

SLIDER
402
814
618
847
LiqDem_TradeLength
LiqDem_TradeLength
30
600
30
30
1
NIL
HORIZONTAL

SLIDER
1130
815
1355
848
LiqDem_ProbBuy
LiqDem_ProbBuy
0
100
49
1
1
NIL
HORIZONTAL

SLIDER
626
814
843
847
LiqDem_ArrivalRate
LiqDem_ArrivalRate
0
1440
600
60
1
NIL
HORIZONTAL

SWITCH
1380
815
1505
848
timeseries
timeseries
0
1
-1000

INPUTBOX
1505
815
1610
875
timeseriesvalue
0
1
0
Number

TEXTBOX
15
890
150
910
Liquidity Supplier
16
0.0
1

SLIDER
175
880
365
913
#_LiqSup
#_LiqSup
0
25
11
1
1
NIL
HORIZONTAL

SLIDER
401
882
619
915
LiqSup_TradeLength
LiqSup_TradeLength
0
1440
1020
60
1
NIL
HORIZONTAL

SLIDER
627
882
842
915
LiqSup_ArrivalRate
LiqSup_ArrivalRate
0
2880
1320
120
1
NIL
HORIZONTAL

SLIDER
857
881
1088
914
LiqSup_OrderSizeMult
LiqSup_OrderSizeMult
1
25
1
1
1
NIL
HORIZONTAL

SLIDER
1129
879
1354
912
LiqSup_PctPriceChange
LiqSup_PctPriceChange
0.25
5
0.25
0.25
1
NIL
HORIZONTAL

TEXTBOX
15
1015
165
1055
High Frequency
16
0.0
1

SLIDER
175
1010
365
1043
#_HftTdr
#_HftTdr
0
50
0
1
1
NIL
HORIZONTAL

SLIDER
400
1010
620
1043
HftTdr_TradeLength
HftTdr_TradeLength
0
3
1
1
1
NIL
HORIZONTAL

TEXTBOX
15
1080
192
1100
Opportunistic
16
0.0
1

SLIDER
175
1075
365
1108
#_OppTdr
#_OppTdr
0
100
0
1
1
NIL
HORIZONTAL

SLIDER
400
1075
619
1108
OppTdr_TradeLength
OppTdr_TradeLength
0
100
39
3
1
NIL
HORIZONTAL

TEXTBOX
20
1270
170
1291
Absolute Trader
16
5.0
1

SLIDER
175
1265
360
1298
#_AbsTdr
#_AbsTdr
0
1
0
1
1
NIL
HORIZONTAL

TEXTBOX
20
1210
170
1231
Ratio Trader
16
0.0
1

SLIDER
175
1205
360
1238
#_RatTdr
#_RatTdr
0
5
1
1
1
NIL
HORIZONTAL

SLIDER
1135
1205
1360
1238
RatTdr_InvRatio
RatTdr_InvRatio
0
500
61
1
1
NIL
HORIZONTAL

SLIDER
1385
1205
1610
1238
RatTdr_ImbalRatio
RatTdr_ImbalRatio
0
5
1
.1
1
NIL
HORIZONTAL

SLIDER
1135
1140
1360
1173
p_weight
p_weight
0
1
0.7
.1
1
NIL
HORIZONTAL

TEXTBOX
20
1335
170
1353
Forced Sell Trader
16
5.0
1

SLIDER
175
1335
363
1368
#_FrcSal
#_FrcSal
0
5
1
1
1
NIL
HORIZONTAL

INPUTBOX
1135
1335
1360
1395
FrcSal_QuantSale
2
1
0
Number

INPUTBOX
1385
1335
1500
1395
FrcSal_PerStartExec
7436
1
0
Number

INPUTBOX
1500
1335
1610
1395
FrcSal_PerEndExec
7440
1
0
Number

MONITOR
1610
1335
1740
1380
Duration of Execution
FrcSal_PerEndExec - FrcSal_PerStartExec
17
1
11

TEXTBOX
15
1145
165
1166
Spoofer Trader\n
16
0.0
1

SLIDER
175
1140
363
1173
#_SpfTdr
#_SpfTdr
0
5
1
1
1
NIL
HORIZONTAL

SLIDER
1385
1140
1610
1173
SpfTdr_BalDistance
SpfTdr_BalDistance
0
1
0.05
.05
1
NIL
HORIZONTAL

@#$#@#$#@
## ## WHAT IS IT?

This is a model of traders (agents) trading in futures market (OFR Exchange), placing orders in to a limit order book.

## ## HOW IT WORKS

At the model set up with a given number of each types of traders and the amount of time they will leave an order into the market, before canceling it.

## ## HOW TO USE IT

Pressing the SETUP button will clear all transcations and initialize the traders.

## ## CREDITS AND REFERENCES

Paddrik, M., Hayes, R., Todd, A., Yang, S., Scherer, W.  & Beling, P.  (2012).  An Agent-based Model of the E-Mini S&P 500 and the Flash Crash.  IEEE Computational Intelligence for Financial Engineering and Economics.

<!-- 1997 2000 -->
@#$#@#$#@
default
true
0
Polygon -7500403 true true 150 5 40 250 150 205 260 250

airplane
true
0
Polygon -7500403 true true 150 0 135 15 120 60 120 105 15 165 15 195 120 180 135 240 105 270 120 285 150 270 180 285 210 270 165 240 180 180 285 195 285 165 180 105 180 60 165 15

arrow
true
0
Polygon -7500403 true true 150 0 0 150 105 150 105 293 195 293 195 150 300 150

box
false
0
Polygon -7500403 true true 150 285 285 225 285 75 150 135
Polygon -7500403 true true 150 135 15 75 150 15 285 75
Polygon -7500403 true true 15 75 15 225 150 285 150 135
Line -16777216 false 150 285 150 135
Line -16777216 false 150 135 15 75
Line -16777216 false 150 135 285 75

bug
true
0
Circle -7500403 true true 96 182 108
Circle -7500403 true true 110 127 80
Circle -7500403 true true 110 75 80
Line -7500403 true 150 100 80 30
Line -7500403 true 150 100 220 30

butterfly
true
0
Polygon -7500403 true true 150 165 209 199 225 225 225 255 195 270 165 255 150 240
Polygon -7500403 true true 150 165 89 198 75 225 75 255 105 270 135 255 150 240
Polygon -7500403 true true 139 148 100 105 55 90 25 90 10 105 10 135 25 180 40 195 85 194 139 163
Polygon -7500403 true true 162 150 200 105 245 90 275 90 290 105 290 135 275 180 260 195 215 195 162 165
Polygon -16777216 true false 150 255 135 225 120 150 135 120 150 105 165 120 180 150 165 225
Circle -16777216 true false 135 90 30
Line -16777216 false 150 105 195 60
Line -16777216 false 150 105 105 60

car
false
0
Polygon -7500403 true true 300 180 279 164 261 144 240 135 226 132 213 106 203 84 185 63 159 50 135 50 75 60 0 150 0 165 0 225 300 225 300 180
Circle -16777216 true false 180 180 90
Circle -16777216 true false 30 180 90
Polygon -16777216 true false 162 80 132 78 134 135 209 135 194 105 189 96 180 89
Circle -7500403 true true 47 195 58
Circle -7500403 true true 195 195 58

circle
false
0
Circle -7500403 true true 0 0 300

circle 2
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240

cow
false
0
Polygon -7500403 true true 200 193 197 249 179 249 177 196 166 187 140 189 93 191 78 179 72 211 49 209 48 181 37 149 25 120 25 89 45 72 103 84 179 75 198 76 252 64 272 81 293 103 285 121 255 121 242 118 224 167
Polygon -7500403 true true 73 210 86 251 62 249 48 208
Polygon -7500403 true true 25 114 16 195 9 204 23 213 25 200 39 123

cylinder
false
0
Circle -7500403 true true 0 0 300

dot
false
0
Circle -7500403 true true 90 90 120

face happy
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 255 90 239 62 213 47 191 67 179 90 203 109 218 150 225 192 218 210 203 227 181 251 194 236 217 212 240

face neutral
false
0
Circle -7500403 true true 8 7 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Rectangle -16777216 true false 60 195 240 225

face sad
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 168 90 184 62 210 47 232 67 244 90 220 109 205 150 198 192 205 210 220 227 242 251 229 236 206 212 183

fish
false
0
Polygon -1 true false 44 131 21 87 15 86 0 120 15 150 0 180 13 214 20 212 45 166
Polygon -1 true false 135 195 119 235 95 218 76 210 46 204 60 165
Polygon -1 true false 75 45 83 77 71 103 86 114 166 78 135 60
Polygon -7500403 true true 30 136 151 77 226 81 280 119 292 146 292 160 287 170 270 195 195 210 151 212 30 166
Circle -16777216 true false 215 106 30

flag
false
0
Rectangle -7500403 true true 60 15 75 300
Polygon -7500403 true true 90 150 270 90 90 30
Line -7500403 true 75 135 90 135
Line -7500403 true 75 45 90 45

flower
false
0
Polygon -10899396 true false 135 120 165 165 180 210 180 240 150 300 165 300 195 240 195 195 165 135
Circle -7500403 true true 85 132 38
Circle -7500403 true true 130 147 38
Circle -7500403 true true 192 85 38
Circle -7500403 true true 85 40 38
Circle -7500403 true true 177 40 38
Circle -7500403 true true 177 132 38
Circle -7500403 true true 70 85 38
Circle -7500403 true true 130 25 38
Circle -7500403 true true 96 51 108
Circle -16777216 true false 113 68 74
Polygon -10899396 true false 189 233 219 188 249 173 279 188 234 218
Polygon -10899396 true false 180 255 150 210 105 210 75 240 135 240

house
false
0
Rectangle -7500403 true true 45 120 255 285
Rectangle -16777216 true false 120 210 180 285
Polygon -7500403 true true 15 120 150 15 285 120
Line -16777216 false 30 120 270 120

leaf
false
0
Polygon -7500403 true true 150 210 135 195 120 210 60 210 30 195 60 180 60 165 15 135 30 120 15 105 40 104 45 90 60 90 90 105 105 120 120 120 105 60 120 60 135 30 150 15 165 30 180 60 195 60 180 120 195 120 210 105 240 90 255 90 263 104 285 105 270 120 285 135 240 165 240 180 270 195 240 210 180 210 165 195
Polygon -7500403 true true 135 195 135 240 120 255 105 255 105 285 135 285 165 240 165 195

line
true
0
Line -7500403 true 150 0 150 300

line half
true
0
Line -7500403 true 150 0 150 150

pentagon
false
0
Polygon -7500403 true true 150 15 15 120 60 285 240 285 285 120

person
false
0
Circle -7500403 true true 110 5 80
Polygon -7500403 true true 105 90 120 195 90 285 105 300 135 300 150 225 165 300 195 300 210 285 180 195 195 90
Rectangle -7500403 true true 127 79 172 94
Polygon -7500403 true true 195 90 240 150 225 180 165 105
Polygon -7500403 true true 105 90 60 150 75 180 135 105

plant
false
0
Rectangle -7500403 true true 135 90 165 300
Polygon -7500403 true true 135 255 90 210 45 195 75 255 135 285
Polygon -7500403 true true 165 255 210 210 255 195 225 255 165 285
Polygon -7500403 true true 135 180 90 135 45 120 75 180 135 210
Polygon -7500403 true true 165 180 165 210 225 180 255 120 210 135
Polygon -7500403 true true 135 105 90 60 45 45 75 105 135 135
Polygon -7500403 true true 165 105 165 135 225 105 255 45 210 60
Polygon -7500403 true true 135 90 120 45 150 15 180 45 165 90

sheep
false
15
Circle -1 true true 203 65 88
Circle -1 true true 70 65 162
Circle -1 true true 150 105 120
Polygon -7500403 true false 218 120 240 165 255 165 278 120
Circle -7500403 true false 214 72 67
Rectangle -1 true true 164 223 179 298
Polygon -1 true true 45 285 30 285 30 240 15 195 45 210
Circle -1 true true 3 83 150
Rectangle -1 true true 65 221 80 296
Polygon -1 true true 195 285 210 285 210 240 240 210 195 210
Polygon -7500403 true false 276 85 285 105 302 99 294 83
Polygon -7500403 true false 219 85 210 105 193 99 201 83

square
false
0
Rectangle -7500403 true true 30 30 270 270

square 2
false
0
Rectangle -7500403 true true 30 30 270 270
Rectangle -16777216 true false 60 60 240 240

star
false
0
Polygon -7500403 true true 151 1 185 108 298 108 207 175 242 282 151 216 59 282 94 175 3 108 116 108

target
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240
Circle -7500403 true true 60 60 180
Circle -16777216 true false 90 90 120
Circle -7500403 true true 120 120 60

tree
false
0
Circle -7500403 true true 118 3 94
Rectangle -6459832 true false 120 195 180 300
Circle -7500403 true true 65 21 108
Circle -7500403 true true 116 41 127
Circle -7500403 true true 45 90 120
Circle -7500403 true true 104 74 152

triangle
false
0
Polygon -7500403 true true 150 30 15 255 285 255

triangle 2
false
0
Polygon -7500403 true true 150 30 15 255 285 255
Polygon -16777216 true false 151 99 225 223 75 224

truck
false
0
Rectangle -7500403 true true 4 45 195 187
Polygon -7500403 true true 296 193 296 150 259 134 244 104 208 104 207 194
Rectangle -1 true false 195 60 195 105
Polygon -16777216 true false 238 112 252 141 219 141 218 112
Circle -16777216 true false 234 174 42
Rectangle -7500403 true true 181 185 214 194
Circle -16777216 true false 144 174 42
Circle -16777216 true false 24 174 42
Circle -7500403 false true 24 174 42
Circle -7500403 false true 144 174 42
Circle -7500403 false true 234 174 42

turtle
true
0
Polygon -10899396 true false 215 204 240 233 246 254 228 266 215 252 193 210
Polygon -10899396 true false 195 90 225 75 245 75 260 89 269 108 261 124 240 105 225 105 210 105
Polygon -10899396 true false 105 90 75 75 55 75 40 89 31 108 39 124 60 105 75 105 90 105
Polygon -10899396 true false 132 85 134 64 107 51 108 17 150 2 192 18 192 52 169 65 172 87
Polygon -10899396 true false 85 204 60 233 54 254 72 266 85 252 107 210
Polygon -7500403 true true 119 75 179 75 209 101 224 135 220 225 175 261 128 261 81 224 74 135 88 99

wheel
false
0
Circle -7500403 true true 3 3 294
Circle -16777216 true false 30 30 240
Line -7500403 true 150 285 150 15
Line -7500403 true 15 150 285 150
Circle -7500403 true true 120 120 60
Line -7500403 true 216 40 79 269
Line -7500403 true 40 84 269 221
Line -7500403 true 40 216 269 79
Line -7500403 true 84 40 221 269

wolf
false
0
Polygon -16777216 true false 253 133 245 131 245 133
Polygon -7500403 true true 2 194 13 197 30 191 38 193 38 205 20 226 20 257 27 265 38 266 40 260 31 253 31 230 60 206 68 198 75 209 66 228 65 243 82 261 84 268 100 267 103 261 77 239 79 231 100 207 98 196 119 201 143 202 160 195 166 210 172 213 173 238 167 251 160 248 154 265 169 264 178 247 186 240 198 260 200 271 217 271 219 262 207 258 195 230 192 198 210 184 227 164 242 144 259 145 284 151 277 141 293 140 299 134 297 127 273 119 270 105
Polygon -7500403 true true -1 195 14 180 36 166 40 153 53 140 82 131 134 133 159 126 188 115 227 108 236 102 238 98 268 86 269 92 281 87 269 103 269 113

x
false
0
Polygon -7500403 true true 270 75 225 30 30 225 75 270
Polygon -7500403 true true 30 75 75 30 270 225 225 270

@#$#@#$#@
NetLogo 5.3.1
@#$#@#$#@
set grass? true
setup
repeat 75 [ go ]
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
default
0.0
-0.2 0 0.0 1.0
0.0 1 1.0 0.0
0.2 0 0.0 1.0
link direction
true
0
Line -7500403 true 150 150 90 180
Line -7500403 true 150 150 210 180

@#$#@#$#@
0
@#$#@#$#@
