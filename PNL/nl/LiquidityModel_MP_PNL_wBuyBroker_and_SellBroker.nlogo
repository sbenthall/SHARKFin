extensions [array table]

;*****************************************************************************************************
;Global Variables
;*****************************************************************************************************
;------------------------------------------------------------------------------
; Variables available globally
;------------------------------------------------------------------------------
Globals [
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
  allOrders                ;List of all orders and order_updates hatched in the current tick cycle
  list_orders              ;List of all orders (but not order_updates) available at the end of current tick cycle
  list_traders             ;List of all traders at the end of the current tick cycle, for the inventory report
  ; endBurninTime            ;Number of burnin ticks -- used to be hard coded as 5,000 -
]
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
  PriceOrder               ;NEED A COMMENT HERE (TODO!!)
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
  random-seed 1
  setup-economy
  file-close-all
  ; set endBurninTime 2000    ;Added by John Liechty 11/17/2020
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
  set ProbabilityBuyofLiqyuidityDemander 49

  set currentOrderBid 399
  set currentOrderAsk 401
  set price 400

  set timeserieslist [200 300 200 0 200 500 300 0 -100 100 100 0 0]
  set timeserieslistcount 0
  set resethillclimbto50 0

  my-setup-plots
  set arrayQ array:from-list n-values 10000 ["B"]
  carefully [file-delete "OrderBook.csv"][]
  carefully [file-delete "OrderBookDepth.csv"][]
  set randNumOT 0
  set period 0
  set tradeExNumber 0
  set numberAsk []
  set numberBid []

  set BuyOrderQueue []
  set SellOrderQueue []
  set numberOrderAsk []
  set numberOrderBid []

  carefully [file-delete "OrderBook.csv"][]
  carefully [file-delete "OrderBookDepth.csv"][]
  carefully [file-delete "AgentData.csv"][]
  carefully [writeFileTitles][]
  carefully [writeFileTitleDepth][]
  carefully [writeFileTitleAgent][]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to setup-economy
  ;Initial Model and Agent Conditions

  ;; turtles procedure for setup
  set traderListNumbers [0]
  create-traders #_LiqDem [LiqDem_Setup]
  create-traders #_MktMkr [MktMkr_Setup]
  create-traders #_LiqSup [LiqSup_Setup]
  create-traders 1        [BkrBuy_Setup]
  create-traders 1        [BkrSel_Setup]
  create-traders 1        [FrcSal_Setup]

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
   if(item countTraderNumber traderListNumbers = traderNumber)[set checkTraderNumber 0]
   if(countTraderNumber = countTradersintradelist) [stop]
   set countTraderNumber (countTraderNumber + 1)
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


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
  ][
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
    if (not is-an-order? ord)         [ report (word index " is dead")       ]
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


;//////////////////////////////////////////////////////////////////////////////
to go
  ;Function run for every tick of the model to advance one time step ahead

  ; The allOrders list holds all orders and order_updates hatched this tick
  ask order_updates [
    die
  ]
  set allOrders []

  set currentBuyInterest 0
  set currentSellInterest 0
  set currentBuyInterestPrice 0
  set currentSellInterestPrice 0

  if((ticks - endBurninTime) mod 1440 = 1439 and ticks > endBurninTime) [
    set timeserieslistcount (timeserieslistcount + 1)
    ]

  if( ticks mod 10 = 0)
  [
    set aggressiveBid 0
    set aggressiveAsk 0
  ]

  ask traders [

    set countticks (countticks + 1)

    if (typeOfTrader = "LiquidityDemander") [
      if countticks >= (LiqDem_TradeLength + tradeSpeedAdjustment) [
        set tradeStatus "Transact"
        if(ticks > endBurninTime) [
          set totalCanceled (totalCanceled + tradeQuantity)
        ]
        set speed int(random-poisson liquidity_Demander_Arrival_Rate) + 1
      ]
    ]

    if (typeOfTrader = "LiqBuyBkr") [
      if ( (countticks >= (5 + tradeSpeedAdjustment)) and ((1.1 * PeriodtoEndExecution) >= ticks) ) [
        set tradeStatus "Transact"
        set speed 5
      ]
    ]

    if (typeOfTrader = "LiqSellBkr") [
      if ( (countticks >= (5 + tradeSpeedAdjustment)) and ((1.1 * PeriodtoEndExecution) >= ticks) ) [
        set tradeStatus "Transact"
        set speed 5
      ]
    ]

;    if (typeOfTrader = "LiqBkr") [
;      if countticks >= (LiqBkr_TradeLength + tradeSpeedAdjustment) [
;        set tradeStatus "Transact"
;        if(ticks > endBurninTime) [
;          set totalCanceled (totalCanceled + tradeQuantity)
;        ]
;        set speed int(random-poisson LiqBkr_ArrivalRate) + 1
;      ]
;    ]

    if (typeOfTrader = "MarketMakers") [
        if countticks >= (MktMkr_TradeLength + tradeSpeedAdjustment) [
          set tradeStatus "Transact"
          set speed int(random-poisson market_Makers_Arrival_Rate) + 2
        ]
    ]

    if (typeOfTrader = "LiquiditySupplier") [
      if countticks >= (LiqSup_TradeLength + tradeSpeedAdjustment)  [
        set tradeStatus "Transact"
        if(ticks > endBurninTime) [
          set totalCanceled (totalCanceled + tradeQuantity)
        ]
        set speed int(random-poisson liquidity_Supplier_Arrival_Rate) + 1
      ]
    ]

    if (typeOfTrader = "ForcedSale" and FrcSal_QuantSale > 0) [
      if ((countticks >= (5 + tradeSpeedAdjustment)) and (PeriodtoStartExecution < ticks) and (PeriodtoEndExecution >= ticks)) [
        set tradeStatus "Transact"
        set speed 5
      ]
    ]


    set tradeAccount ((sharesOwned * ( price / 4) - averageBoughtPrice * totalBought + averageSoldPrice * totalSold) - (transactionCost * (totalBought + totalSold)))

    if((typeOfTrader = "LiquidityDemander" or
        typeOfTrader = "LiquiditySupplier" or
        typeOfTrader = "MarketMakers" or
        typeOfTrader = "LiqBuyBkr" or
        typeOfTrader = "LiqSellBkr") and
        tradeStatus = "Buy" and tradeQuantity > 0) [
      set currentBuyInterestPrice ((currentBuyInterestPrice * currentBuyInterest + tradeQuantity * tradePrice) / (currentBuyInterest + tradeQuantity))
      set currentBuyInterest (currentBuyInterest + tradeQuantity)
    ]

    if((typeOfTrader = "LiquidityDemander" or
        typeOfTrader = "LiquiditySupplier" or
        typeOfTrader = "MarketMakers" ) and
        tradeStatus = "Sell" and tradeQuantity > 0) [
      set currentSellInterestPrice ((currentSellInterestPrice * currentSellInterest + tradeQuantity * tradePrice) / (currentSellInterest + tradeQuantity))
      set currentSellInterest (currentSellInterest + tradeQuantity)
    ]

    if (tradeStatus = "Transact")[
      if countticks > (speed + tradeSpeedAdjustment)  [
        set countticks 0
        set modify 0

        if (typeOfTrader = "LiqBuyBkr") [
          BkrBuyStrategy
        ]
        if (typeOfTrader = "LiqSellBkr") [
          BkrSelStrategy
        ]
        if (typeOfTrader = "LiquidityDemander") [
          LiqDem_strategy
        ]
        if (typeOfTrader = "MarketMakers") [
          MktMkr_strategy
        ]
        if (typeOfTrader = "LiquiditySupplier") [
          LiqSup_strategy
        ]
        if (typeOfTrader = "ForcedSale") [
          FrcSal_strategy
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

      let transactionVar 0

      if (ticks > endBurninTime ) [
        transactionOrder
      ]
    ]
  ]

  if ( count orders with [OrderB/A = "Buy"] > 0 ) [
    set numberOrderBid []
    histoSetupTestBuy
    setup-plot2
  ]

  if ( count orders with [OrderB/A = "Sell"] > 0 ) [
    set numberOrderAsk []
    histoSetupTestSell
  ]

  do-plots

  if(ticks >= endBurninTime) [
    if((ticks - 4700) mod 600 = 0 ) [
      calculatePriceReturns
    ]
  ]

  if(ticks > 12000) [
    set minPriceValue min movingAverage
  ]
  if(DepthFile = true and ticks > 4999)[
    writetofiledepth
  ]
  if(AgentFile = true and ticks > 4999)[
    writetofileagent
  ]

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

;        if(AuditTrail = true) [
;          set MatchID (MatchID + 1)
;          writetofile orderBidID "Bought" price orderQuantityBid traderBidType traderBidNum 1 MatchID orderHON1Bid orderHON2Bid
;          writetofile orderAskID "Sold" price orderQuantityAsk traderAskType traderAskNum 2 MatchID orderHON1Ask orderHON2Ask
;        ]

        ask traderBid [ set sharesOwned (sharesOwned + orderQuantityBid) set averageBoughtPrice ((averageBoughtPrice * totalBought + (price / 4) * orderQuantityBid) / (totalBought + orderQuantityBid)) set totalBought (totalBought + orderQuantityBid) ]
        ask traderAsk [ set sharesOwned (sharesOwned - orderQuantityAsk) set averageSoldPrice ((averageSoldPrice * totalSold + (price / 4) * orderQuantityAsk) / (totalSold + orderQuantityAsk)) set totalSold (totalSold + orderQuantityAsk)]
        set volume (volume + orderQuantityAsk)

      ]

      if ( quantityDiff > 0 ) [

        ask firstInBuyQueue [
          set OrderQuantity quantityDiff
        ]
        ask traderBid [
          set traderBidNum traderNumber set traderBidType typeOfTrader
        ]
        ask traderAsk [
          set openorders remove firstInSellQueue openorders set traderAskNum traderNumber set traderAskType typeOfTrader
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

;        if(AuditTrail = true) [
;          set MatchID (MatchID + 1)
;          writetofile orderBidID "Bought" price orderQuantityAsk traderBidType traderBidNum 1 MatchID orderHON1Bid orderHON2Bid
;          writetofile orderAskID "Sold" price orderQuantityAsk traderAskType traderAskNum 2 MatchID orderHON1Ask orderHON2Ask
;        ]

        ask traderBid [ set sharesOwned (sharesOwned + orderQuantityAsk)
          set averageBoughtPrice ((averageBoughtPrice * totalBought + (price / 4) * orderQuantityAsk) / (totalBought + orderQuantityAsk)) set totalBought (totalBought + orderQuantityAsk)]

        ask traderAsk [ set sharesOwned (sharesOwned - orderQuantityAsk)
          set averageSoldPrice ((averageSoldPrice * totalSold + (price / 4) * orderQuantityAsk) / (totalSold + orderQuantityAsk)) set totalSold (totalSold + orderQuantityAsk)  ]
        set volume (volume + orderQuantityAsk)

        transactionOrder
      ]

      if ( quantityDiff < 0 ) [

        ask traderBid [ set openorders remove firstInBuyQueue openorders set traderBidNum traderNumber set traderBidType typeOfTrader]
        ask firstInSellQueue [ set OrderQuantity ( -1 * quantityDiff) ]
        ask traderAsk [ set traderAskNum traderNumber set traderAskType typeOfTrader]
        ask firstInBuyQueue [ die ]

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

        ask traderBid [ set sharesOwned (sharesOwned + orderQuantityBid) set averageBoughtPrice ((averageBoughtPrice * totalBought + (price / 4) * orderQuantityBid) / (totalBought + orderQuantityBid)) set totalBought (totalBought + orderQuantityBid)]
        ask traderAsk [ set sharesOwned (sharesOwned - orderQuantityBid) set averageSoldPrice ((averageSoldPrice * totalSold + (price / 4) * orderQuantityBid) / (totalSold + orderQuantityBid)) set totalSold (totalSold + orderQuantityBid)]
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
;============ market_maker_agent BEHAVIORAL SPECIFICATION =====================
;==============================================================================
;//////////////////////////////////////////////////////////////////////////////
;; Setup for Trader
;******************************************************************************
to MktMkr_Setup
  set typeOfTrader "MarketMakers"
  set speed 1000
  set tradeSpeedAdjustment random 10    set tradeStatus "Transact"
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
  set tradeQuantity 5 * marketMakerOrderSizeMultipler
  if(sharesOwned > (MarketMakerInventoryLimit / 5))[set tradeQuantity 4 * marketMakerOrderSizeMultipler]
  if(sharesOwned > (MarketMakerInventoryLimit * 2 / 5))[set tradeQuantity 3 * marketMakerOrderSizeMultipler]
  if(sharesOwned > (MarketMakerInventoryLimit * 3 / 5))[set tradeQuantity 2 * marketMakerOrderSizeMultipler]
  if(sharesOwned > (MarketMakerInventoryLimit * 4 / 5))[set tradeQuantity 1 * marketMakerOrderSizeMultipler]
  if(sharesOwned > (MarketMakerInventoryLimit))[set tradeQuantity 0 * marketMakerOrderSizeMultipler]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to MktMkr_distOrderSell
  set tradeQuantity 5 * marketMakerOrderSizeMultipler
  if(sharesOwned < (-1 * (MarketMakerInventoryLimit / 5)))[set tradeQuantity 4 * marketMakerOrderSizeMultipler]
  if(sharesOwned < (-1 * (MarketMakerInventoryLimit * 2 / 5)))[set tradeQuantity 3 * marketMakerOrderSizeMultipler]
  if(sharesOwned < (-1 * (MarketMakerInventoryLimit * 3 / 5)))[set tradeQuantity 2 * marketMakerOrderSizeMultipler]
  if(sharesOwned < (-1 * (MarketMakerInventoryLimit * 4 / 5)))[set tradeQuantity 1 * marketMakerOrderSizeMultipler]
  if(sharesOwned < (-1 * (MarketMakerInventoryLimit)))[set tradeQuantity 0 * marketMakerOrderSizeMultipler]
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

        ifelse table:has-key? OrderCheckList OrderPriceDelta [

          if OrderQuantity != table:get OrderCheckList OrderPriceDelta [
            set orderNumber (orderNumber + 1)
            set OrderQuantity table:get OrderCheckList OrderPriceDelta
            set PriceOrder (OrderPrice * 100000000000) + orderNumber
            set HON2 HON1
            set HON1 (HON1 + 1)

;            if(AuditTrail = true) [
;              writetofile OrderID "Modify" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;            ]
            hatch-order_updates 1 [Order_Update OrderID OrderPrice "Modify" tradernumber OrderQuantity TraderWho TraderWhoType]
          ]

          table:remove OrderCheckList OrderPriceDelta
        ][
          let OrderCancel OrderQuantity
          ask TraderWho [
            set openorders remove ? openorders
            set totalCanceled (totalCanceled + OrderCancel)
          ]

;          if(AuditTrail = true) [
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
        ][
          let OrderCancel OrderQuantity
          ask TraderWho [ set openorders remove ? openorders set totalCanceled (totalCanceled + OrderCancel)]

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
    ][
      set BuySellDecision "Sell"
    ]

    if table:has-key? OrderCheckList i [
      ifelse BuySellDecision = "Buy" [
        hatch-orders 1 [Order_Setup (price - (i - 1)) BuySellDecision traderNumber (table:get OrderCheckList i) myself typeOfTrader]
      ][
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
 ifelse((count turtles with [typeOfTrader = "MarketMakers"]) > 0)
 [report precision (((sum [sharesOwned] of traders with [typeOfTrader = "MarketMakers"])) / (count traders with [typeOfTrader = "MarketMakers"]))  2
 ][report 0]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report MktMkr_accountValue
  ifelse((count turtles with [typeOfTrader = "MarketMakers"]) > 0)
  [report precision ((sum [tradeAccount] of traders with [typeOfTrader = "MarketMakers"]) / (count traders with [typeOfTrader = "MarketMakers"])) 2
  ][report 0]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;==============================================================================
;========= liquidity_demander_agent BEHAVIORAL SPECIFICATION ==================
;==============================================================================
;code by Mark Paddrik
;//////////////////////////////////////////////////////////////////////////////
to LiqDem_Setup
  set typeOfTrader "LiquidityDemander"
  set speed (random-poisson liquidity_Demander_Arrival_Rate) + 1
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
  let randDraw random 100
  set tradeQuantity 1 * liquidityDemanderOrderSizeMultipler
  if(randDraw > 31)[set tradeQuantity 2 * liquidityDemanderOrderSizeMultipler]
  if(randDraw > 50)[set tradeQuantity 3 * liquidityDemanderOrderSizeMultipler]
  if(randDraw > 63)[set tradeQuantity 4 * liquidityDemanderOrderSizeMultipler]
  if(randDraw > 73)[set tradeQuantity 5 * liquidityDemanderOrderSizeMultipler]
  if(randDraw > 82)[set tradeQuantity 6 * liquidityDemanderOrderSizeMultipler]
  if(randDraw > 94)[set tradeQuantity 7 * liquidityDemanderOrderSizeMultipler]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to LiqDem_distPriceBuy
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

  if(timeseries = True and ticks > endBurninTime)
  [
    if sum [sharesOwned] of traders with [typeOfTrader = "LiquidityDemander"] < timeseriesvalue [
       if (resethillclimbto50 = -1)[
         set ProbabilityBuyofLiqyuidityDemander 50
       ]
       set resethillclimbto50 1
       set ProbabilityBuyofLiqyuidityDemander (ProbabilityBuyofLiqyuidityDemander + (sqrt(100 - ProbabilityBuyofLiqyuidityDemander)) / 100)
    ]
    if sum [sharesOwned] of traders with [typeOfTrader = "LiquidityDemander"] > timeseriesvalue [
       if (resethillclimbto50 = 1)[
         set ProbabilityBuyofLiqyuidityDemander 50
       ]
       set resethillclimbto50 -1
       set ProbabilityBuyofLiqyuidityDemander (ProbabilityBuyofLiqyuidityDemander - (sqrt(abs(ProbabilityBuyofLiqyuidityDemander))) / 100)
    ]
  ]

  let randDraw random 10000
  ifelse randDraw < ((ProbabilityBuyofLiqyuidityDemander * 100) + 125) [
     set tradeStatus "Buy"
     LiqDem_distPriceBuy
     LiqDem_distOrder
  ][
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
 ifelse((count turtles with [typeOfTrader = "LiquidityDemander"]) > 0)
 [report precision (((sum [sharesOwned] of traders with [typeOfTrader = "LiquidityDemander"])) / (count traders with [typeOfTrader = "LiquidityDemander"]))  2
 ][report 0]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report LiqDem_accountValue
  ifelse((count turtles with [typeOfTrader = "LiquidityDemander"]) > 0)
  [report precision ((sum [tradeAccount] of traders with [typeOfTrader = "LiquidityDemander"]) / (count traders with [typeOfTrader = "LiquidityDemander"])) 2
  ][report 0]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;==============================================================================
;========= liquidity_supplier_agent BEHAVIORAL SPECIFICATION ==================
;==============================================================================
;//////////////////////////////////////////////////////////////////////////////
to LiqSup_Setup
  set typeOfTrader "LiquiditySupplier"
  set speed (random-poisson liquidity_Supplier_Arrival_Rate) + 1
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
  let priceChange ((price / 4) - 100)

  let multipleSizePrice (precision ((-1 * priceChange) / PercentPriceChangetoOrderSizeMultiple) 0) + 1

  if (multipleSizePrice <= 0) [set multipleSizePrice 1]

  let randDraw random 100
  set tradeQuantity 1 * liquiditySupplierOrderSizeMultipler * multipleSizePrice
  if(randDraw > 32)[set tradeQuantity 2 * liquiditySupplierOrderSizeMultipler * multipleSizePrice]
  if(randDraw > 50)[set tradeQuantity 3 * liquiditySupplierOrderSizeMultipler * multipleSizePrice]
  if(randDraw > 63)[set tradeQuantity 4 * liquiditySupplierOrderSizeMultipler * multipleSizePrice]
  if(randDraw > 73)[set tradeQuantity 5 * liquiditySupplierOrderSizeMultipler * multipleSizePrice]
  if(randDraw > 82)[set tradeQuantity 6 * liquiditySupplierOrderSizeMultipler * multipleSizePrice]
  if(randDraw > 94)[set tradeQuantity 7 * liquiditySupplierOrderSizeMultipler * multipleSizePrice]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to LiqSup_distOrderSell
  let priceChange ((price / 4) - 100)

  let multipleSizePrice (precision ((priceChange) / PercentPriceChangetoOrderSizeMultiple) 0) + 1

  if (multipleSizePrice <= 0) [set multipleSizePrice 1]

  let randDraw random 100
  set tradeQuantity 1 * liquiditySupplierOrderSizeMultipler * multipleSizePrice
  if(randDraw > 32)[set tradeQuantity 2 * liquiditySupplierOrderSizeMultipler * multipleSizePrice]
  if(randDraw > 50)[set tradeQuantity 3 * liquiditySupplierOrderSizeMultipler * multipleSizePrice]
  if(randDraw > 63)[set tradeQuantity 4 * liquiditySupplierOrderSizeMultipler * multipleSizePrice]
  if(randDraw > 73)[set tradeQuantity 5 * liquiditySupplierOrderSizeMultipler * multipleSizePrice]
  if(randDraw > 82)[set tradeQuantity 6 * liquiditySupplierOrderSizeMultipler * multipleSizePrice]
  if(randDraw > 94)[set tradeQuantity 7 * liquiditySupplierOrderSizeMultipler * multipleSizePrice]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to LiqSup_distPriceBuy
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

  let randDraw random 10000
  ifelse randDraw < 5000 [
     set tradeStatus "Buy"
     LiqSup_distPriceBuy
     LiqSup_distOrderBuy
  ][
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
 ifelse((count turtles with [typeOfTrader = "LiquiditySupplier"]) > 0)
 [report precision (((sum [sharesOwned] of traders with [typeOfTrader = "LiquiditySupplier"])) / (count traders with [typeOfTrader = "LiquiditySupplier"]))  2
 ][report 0]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report LiqSup_accountValue
  ifelse((count turtles with [typeOfTrader = "LiquiditySupplier"]) > 0)
  [report precision ((sum [tradeAccount] of traders with [typeOfTrader = "LiquiditySupplier"]) / (count traders with [typeOfTrader = "LiquiditySupplier"])) 2
  ][report 0]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;==============================================================================
;========== liquidity_sell_broker_agent BEHAVIORAL SPECIFICATION ==============
;==============================================================================

;******************************************************************************
; Setup for Trader
;------------------------------------------------------------------------------
to BkrSel_Setup
  set typeOfTrader "LiqSellBkr"
  ;Testing Speed
  ;set speed 0
  ;set tradeSpeedAdjustment (random 30) + 1
  set speed (random-poisson 5)
  set tradeSpeedAdjustment 1
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
;code by John Liechty
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to BkrSelStrategy
  foreach openorders [
    ask ?[
;      if(AuditTrail = true)[
;        writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;      ]
      die
    ]
  ]

  set openorders []


  let tSharesOwned sum [sharesOwned] of traders with [typeOfTrader = "LiqSellBkr"]
  let negSell_Limit (-1) * BkrSel_Limit
  ifelse( tSharesOwned >= negSell_Limit )[

   set tradeStatus "Sell"
   set tradePrice price - 5
   let rDraw random 100
   let pctTimeLeft (PeriodtoEndExecution - ticks) / (PeriodtoEndExecution - endBurninTime)
   ifelse(PeriodtoEndExecution <= ticks)[
     set tradeQuantity round ( ( (LiqBkr_OrderSizeMultiplier * (1 - (0.5 * pctTimeLeft))) * (pctTimeLeft * (rDraw / 100) + 1 - (0.5 * pctTimeLeft)) ) * ( (tSharesOwned - negSell_Limit)) )
     ;set tradeQuantity round (LiqBkr_OrderSizeMultiplier * ( (tSharesOwned - negSell_Limit) ) )
   ][
     set tradeQuantity round ( ( (LiqBkr_OrderSizeMultiplier * (1 - (0.5 * pctTimeLeft))) * (pctTimeLeft * (rDraw / 100) + 1 - (0.5 * pctTimeLeft)) ) * ( (tSharesOwned - negSell_Limit) / (PeriodtoEndExecution - ticks)) )
     ;set tradeQuantity round (LiqBkr_OrderSizeMultiplier * ( (tSharesOwned - negSell_Limit) / (PeriodtoEndExecution - ticks) ) )
   ]

   ;ifelse ( tSharesOwned >= negSell_Limit  )[
   ;  set tradeQuantity 100
   ; ][
   ;' set tradeQuantity 0
   ; ]

   ;Prevent Broker from crossing inventory limit
   if( (tSharesOwned - tradeQuantity)  < negSell_Limit )[
    set tradeQuantity (tSharesOwned - negSell_Limit)
   ]

   if(tradeQuantity < 0)[
     set tradeQuantity 0
   ]

  ][

    set tradeStatus "Buy"
    set tradePrice price + 5
    set tradeQuantity (negSell_Limit - tSharesOwned)

  ]

  hatch-orders 1 [Order_Setup tradePrice tradeStatus traderNumber tradeQuantity myself typeOfTrader]
end
;code by John Liechty
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report avgSharesBkrSel
 ifelse((count turtles with [typeOfTrader = "LiqSellBkr"]) > 0)
 [report precision (((sum [sharesOwned] of traders with [typeOfTrader = "LiqSellBkr"])) / (count traders with [typeOfTrader = "LiqSellBkr"]))  2
 ][report 0]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report accountValueBkrSel
  ifelse((count turtles with [typeOfTrader = "LiqSellBkr"]) > 0)
  [report precision ((sum [tradeAccount] of traders with [typeOfTrader = "LiqSellBkr"]) / (count traders with [typeOfTrader = "LiqSellBkr"])) 2
  ][report 0]
end
;code by John Liechty

;==============================================================================
;=========== liquidity_buy_broker_agent BEHAVIORAL SPECIFICATION ==============
;==============================================================================

;******************************************************************************
; Setup for Trader
;------------------------------------------------------------------------------
to BkrBuy_Setup
  set typeOfTrader "LiqBuyBkr"
  ;Testing Speed
  ;set speed (random-poisson BkrBuy_ArrivalRate) + 1
  set speed (random-poisson 5)
  set tradeSpeedAdjustment 1
  ;set speed 0
  ;set tradeSpeedAdjustment (random 30) + 1
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
;code by Mark Flood
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to BkrBuyStrategy
  foreach openorders [
    ask ?[
;      if(AuditTrail = true)[
;        writetofile OrderID "Cancel" OrderPrice OrderQuantity TraderWhoType tradernumber 1 "-" HON1 HON2
;      ]
      die
    ]
  ]

  set openorders []


  let tSharesOwned sum [sharesOwned] of traders with [typeOfTrader = "LiqBuyBkr"]
  ifelse((tSharesOwned) < BkrBuy_Limit)[

   set tradeStatus "Buy"
   set tradePrice price + 5
   let rDraw random 100
   let pctTimeLeft (PeriodtoEndExecution - ticks) / (PeriodtoEndExecution - endBurninTime)
   ifelse(PeriodtoEndExecution <= ticks)[
     set tradeQuantity round ( ( (LiqBkr_OrderSizeMultiplier * (1 - (0.5 * pctTimeLeft))) * (pctTimeLeft * (rDraw / 100) + 1 - (0.5 * pctTimeLeft)) ) * ( (BkrBuy_Limit - (tSharesOwned))) )
     ;set tradeQuantity round (LiqBkr_OrderSizeMultiplier * ( (BkrBuy_Limit - (tSharesOwned)) ) )
   ][
     set tradeQuantity round ( ( (LiqBkr_OrderSizeMultiplier * (1 - (0.5 * pctTimeLeft))) * (pctTimeLeft * (rDraw / 100) + 1 - (0.5 * pctTimeLeft)) ) * ( (BkrBuy_Limit - (tSharesOwned)) / (PeriodtoEndExecution - ticks)) )
     ;set tradeQuantity round (LiqBkr_OrderSizeMultiplier * ( (BkrBuy_Limit - (tSharesOwned)) / (PeriodtoEndExecution - ticks) ) )
   ]
   ; Prevent Broker from crossing inventory limit
   if(tradeQuantity + (tSharesOwned)  > BkrBuy_Limit)[
    set tradeQuantity (BkrBuy_Limit - (tSharesOwned))

   ]

   if(tradeQuantity < 0)[
     set tradeQuantity 0
   ]

  ][

    set tradeStatus "Sell"
    set tradePrice price - 5
    set tradeQuantity ((tSharesOwned) - BkrBuy_Limit)

  ]

  hatch-orders 1 [Order_Setup tradePrice tradeStatus traderNumber tradeQuantity myself typeOfTrader]
end
;code by Mark Flood
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report avgSharesBkrBuy
 ifelse((count turtles with [typeOfTrader = "LiqBuyBkr"]) > 0)
 [report precision (((sum [sharesOwned] of traders with [typeOfTrader = "LiqBuyBkr"])) / (count traders with [typeOfTrader = "LiqBuyBkr"]))  2
 ][report 0]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report accountValueBkrBuy
  ifelse((count turtles with [typeOfTrader = "LiqBuyBkr"]) > 0)
  [report precision ((sum [tradeAccount] of traders with [typeOfTrader = "LiqBuyBkr"]) / (count traders with [typeOfTrader = "LiqBuyBkr"])) 2
  ][report 0]
end
;code by Mark Flood


;==============================================================================
;============= forced_sale_agent BEHAVIORAL SPECIFICATION =====================
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
     set tradeQuantity round ( (FrcSal_QuantSale + sharesOwned) / ((PeriodtoEndExecution - ticks) / 6))

  hatch-orders 1 [Order_Setup tradePrice tradeStatus traderNumber tradeQuantity myself typeOfTrader]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report FrcSal_avgShares
 ifelse((count turtles with [typeOfTrader = "LiquiditySupplier"]) > 0)
 [report precision (((sum [sharesOwned] of traders with [typeOfTrader = "ForcedSale"])) / (count traders with [typeOfTrader = "ForcedSale"])) 2
 ][report 0]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report FrcSal_accountValue
  ifelse((count turtles with [typeOfTrader = "LiquiditySupplier"]) > 0)
  [report precision ((sum [tradeAccount] of traders with [typeOfTrader = "ForcedSale"]) / (count traders with [typeOfTrader = "ForcedSale"])) 2
  ][report 0]
end
;code by Mark Paddrik




;==============================================================================
;==============================================================================
;==============================================================================
;================= DUMPING PROGRESS, TO VARIOUS LOGS ==========================
;==============================================================================
;==============================================================================
;==============================================================================

;//////////////////////////////////////////////////////////////////////////////
to writeFileTitleAgent
  ;Writing AGENT AUDIT TRAIL to CSV File
  file-open "AgentData.csv"
  file-type "Time"
  foreach sort traders [
  ask ?[
        file-type ", "
        file-type typeOfTrader
        file-type who
     ]
  ]
  file-print ", "
  file-close
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to writetofileagent
  file-open "AgentData.csv"
  file-type hourOutput ;TIME
  file-type ":"
  file-type minute

  foreach sort traders [
    ask ?[
          file-type ", "
          file-type sharesOwned
       ]
    ]

  ifelse (frequency 10975 numberOrderBid > 0) [file-type (-1 * frequency 10975 numberOrderBid) ][file-type frequency 10975 numberOrderAsk]
  file-print ", "
  file-close
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to writeFileTitles
  ; Writing AUDIT TRAIL to CSV File
  ; line output: ORDER ID| HON1 | HON2 | ACCOUNT | BUYSELL | FUNCCODE | TIME | CTI | ASKPRICE | ASKQUANTITY | BIDPRICE | BIDQUANTITY | EXCHANGE | MAX SHOW FLAG | MATCH NUMBER | TANSACTION ID
    file-open "OrderBook.csv"
    file-type "ORDER ID"
    file-type ", "
    file-type "HON1"
    file-type ", "
    file-type "HON2"
    file-type ", "
    file-type "ACCOUNT"
    file-type ", "
    file-type "BUYSELL"
    file-type ", "
    file-type "FUNCCODE"
    file-type ", "
    file-type "PRICE"
    file-type ", "
    file-type "QUANTITY"
    file-type ", "
    file-type "TIME"
    file-type ", "
    file-type "CONFTIME"
    file-type ", "
    file-type "CTI"
    file-type ", "
    file-type "ASKPRICE"
    file-type ", "
    file-type "ASKQUANTITY"
    file-type ", "
    file-type "BIDPRICE"
    file-type ", "
    file-type "BIDQUANTITY"
    file-type ", "
    file-type "EXCHANGE"
    file-type ", "
    file-type "MAX SHOW FLAG"
    file-type ", "
    file-type "MATCH NUMBER"
    file-type ", "
    file-type "TRANSACTION ID"
    file-print ", "
    file-close
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to writetofile [ OID Action TradedPrice q traderType TID OrderBuyOrSell? matchnumber aHON1 aHON2]
  set tradeExNumber (1 + tradeExNumber)

  let newCurrentBidPrice 0
  let newCurrentAskPrice 0

  if count orders with [OrderB/A = "Buy"] > 0 and count orders with [OrderB/A = "Sell"] > 0 [
      let newFirstBuy first (sort-on [(- PriceOrder)] orders with [OrderB/A = "Buy"] )
      let newFirstSell first (sort-on [PriceOrder] orders with [OrderB/A = "Sell"])

      ask newFirstBuy [
        set newCurrentBidPrice OrderPrice
      ]

      ask newFirstSell [
        set newCurrentAskPrice OrderPrice
      ]
    ]

  file-open "OrderBook.csv"
  file-type OID
  file-type ", "
  file-type aHON1 ;HON1
  file-type ", "
  file-type aHON2 ;HON2
  file-type ", "
  file-type TID ;FIRM
  file-type ", "
  file-type OrderBuyOrSell? ;BUYSELL
  file-type ", "
  if(Action = "Buy" or Action = "Sell" )
  [
    file-type "001" ;FUNCCODE
    file-type ", "
  ]
  if(Action = "Bought" or Action = "Sold" )
  [
    file-type "105" ;FUNCCODE
    file-type ", "
  ]
  if(Action = "Cancel" )
  [
    file-type "003" ;FUNCCODE
    file-type ", "
  ]
  if(Action = "Modify" )
  [
    file-type "002" ;FUNCCODE
    file-type ", "
  ]
  file-type ((TradedPrice / 4 + 1000)) ;PRICE
  file-type ", "
  file-type q ;QUANTITY
  file-type ", "
  file-type hourOutput ;TIME
  file-type ":"
  file-type minute
  file-type ", "
  file-type hourOutput ;CONFTIME
  file-type ":"
  file-type minute
  file-type ", "
  if(traderType = "LiquidityDemander")
  [
    file-type "1" ;CTI
    file-type ", "
  ]
  if(traderType = "MarketMakers")
  [
    file-type "2" ;CTI
    file-type ", "
  ]
  if(traderType = "LiquiditySupplier")
  [
    file-type "3" ;CTI
    file-type ", "
  ]
  file-type ((newCurrentAskPrice / 4 + 1000)) ;ASKPRICE
  file-type ", "
  set numberOrderAsk []
  histoSetupTestSell
  file-type occurrences (((newCurrentAskPrice / 4) * 100) + 100000) numberOrderAsk ;ASKQUANTITY
  file-type ", "
  file-type ((newCurrentBidPrice / 4 + 1000)) ;BIDPRICE
  file-type ", "
  set numberOrderBid []
  histoSetupTestBuy
  file-type occurrences (((newCurrentBidPrice / 4) * 100) + 100000) numberOrderBid ;BIDQUANTITY
  file-type ", "
  file-type "OFR" ;EXCHANGE
  file-type ", "
  file-type "-" ;MAX SHOW FLAG
  file-type ", "
  file-type matchnumber ;Match ID
  file-type ", "
  file-type tradeExNumber ;TRANSACTION ID
  file-print ", "
  file-close
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to writeFileTitleDepth
  ; Writing ORDERBOOK DEPTH to CSV File
    file-open "OrderBookDepth.csv"
    file-type "Time"
    file-type ", "
    file-type "80"
    file-type ", "
    file-type "80.25"
    file-type ", "
    file-type "80.50"
    file-type ", "
    file-type "80.75"
    file-type ", "
    file-type "81"
    file-type ", "
    file-type "81.25"
    file-type ", "
    file-type "81.50"
    file-type ", "
    file-type "81.75"
    file-type ", "
    file-type "82"
    file-type ", "
    file-type "82.25"
    file-type ", "
    file-type "82.50"
    file-type ", "
    file-type "82.75"
    file-type ", "
    file-type "83"
    file-type ", "
    file-type "83.25"
    file-type ", "
    file-type "83.50"
    file-type ", "
    file-type "83.75"
    file-type ", "
    file-type "84"
    file-type ", "
    file-type "84.25"
    file-type ", "
    file-type "84.50"
    file-type ", "
    file-type "84.75"
    file-type ", "
    file-type "85"
    file-type ", "
    file-type "85.25"
    file-type ", "
    file-type "85.50"
    file-type ", "
    file-type "85.75"
    file-type ", "
    file-type "86"
    file-type ", "
    file-type "86.25"
    file-type ", "
    file-type "86.50"
    file-type ", "
    file-type "86.75"
    file-type ", "
    file-type "87"
    file-type ", "
    file-type "87.25"
    file-type ", "
    file-type "87.50"
    file-type ", "
    file-type "87.75"
    file-type ", "
    file-type "88"
    file-type ", "
    file-type "88.25"
    file-type ", "
    file-type "88.50"
    file-type ", "
    file-type "88.75"
    file-type ", "
    file-type "89"
    file-type ", "
    file-type "89.25"
    file-type ", "
    file-type "89.50"
    file-type ", "
    file-type "89.75"
    file-type ", "
    file-type "90"
    file-type ", "
    file-type "90.25"
    file-type ", "
    file-type "90.50"
    file-type ", "
    file-type "90.75"
    file-type ", "
    file-type "91"
    file-type ", "
    file-type "91.25"
    file-type ", "
    file-type "91.50"
    file-type ", "
    file-type "91.75"
    file-type ", "
    file-type "92"
    file-type ", "
    file-type "92.25"
    file-type ", "
    file-type "92.50"
    file-type ", "
    file-type "92.75"
    file-type ", "
    file-type "93"
    file-type ", "
    file-type "93.25"
    file-type ", "
    file-type "93.50"
    file-type ", "
    file-type "93.75"
    file-type ", "
    file-type "94"
    file-type ", "
    file-type "94.25"
    file-type ", "
    file-type "94.50"
    file-type ", "
    file-type "94.75"
    file-type ", "
    file-type "95"
    file-type ", "
    file-type "95.25"
    file-type ", "
    file-type "95.50"
    file-type ", "
    file-type "95.75"
    file-type ", "
    file-type "96"
    file-type ", "
    file-type "96.25"
    file-type ", "
    file-type "96.50"
    file-type ", "
    file-type "96.75"
    file-type ", "
    file-type "97"
    file-type ", "
    file-type "97.25"
    file-type ", "
    file-type "97.50"
    file-type ", "
    file-type "97.75"
    file-type ", "
    file-type "98"
    file-type ", "
    file-type "98.25"
    file-type ", "
    file-type "98.50"
    file-type ", "
    file-type "98.75"
    file-type ", "
    file-type "99"
    file-type ", "
    file-type "99.25"
    file-type ", "
    file-type "99.50"
    file-type ", "
    file-type "99.75"
    file-type ", "
    file-type "100"
    file-type ", "
    file-type "100.25"
    file-type ", "
    file-type "100.50"
    file-type ", "
    file-type "100.75"
    file-type ", "
    file-type "101"
    file-type ", "
    file-type "101.25"
    file-type ", "
    file-type "101.50"
    file-type ", "
    file-type "101.75"
    file-type ", "
    file-type "102"
    file-type ", "
    file-type "102.25"
    file-type ", "
    file-type "102.50"
    file-type ", "
    file-type "102.75"
    file-type ", "
    file-type "103"
    file-type ", "
    file-type "103.25"
    file-type ", "
    file-type "103.50"
    file-type ", "
    file-type "103.75"
    file-type ", "
    file-type "104"
    file-type ", "
    file-type "104.25"
    file-type ", "
    file-type "104.50"
    file-type ", "
    file-type "104.75"
    file-type ", "
    file-type "105"
    file-type ", "
    file-type "105.25"
    file-type ", "
    file-type "105.50"
    file-type ", "
    file-type "105.75"
    file-type ", "
    file-type "106"
    file-type ", "
    file-type "106.25"
    file-type ", "
    file-type "106.50"
    file-type ", "
    file-type "106.75"
    file-type ", "
    file-type "107"
    file-type ", "
    file-type "107.25"
    file-type ", "
    file-type "107.50"
    file-type ", "
    file-type "107.75"
    file-type ", "
    file-type "108"
    file-type ", "
    file-type "108.25"
    file-type ", "
    file-type "108.50"
    file-type ", "
    file-type "108.75"
    file-type ", "
    file-type "109"
    file-type ", "
    file-type "109.25"
    file-type ", "
    file-type "109.50"
    file-type ", "
    file-type "109.75"
    file-print ", "
    file-close
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to writetofiledepth
  file-open "OrderBookDepth.csv"
  file-type hourOutput ;TIME
  file-type ":"
  file-type minute
  file-type ", "
  ifelse (frequency 8000 numberOrderBid > 0) [file-type (-1 * frequency 8000 numberOrderBid) ][file-type frequency 8000 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8025 numberOrderBid > 0) [file-type (-1 * frequency 8025 numberOrderBid) ][file-type frequency 8025 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8050 numberOrderBid > 0) [file-type (-1 * frequency 8050 numberOrderBid) ][file-type frequency 8050 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8075 numberOrderBid > 0) [file-type (-1 * frequency 8075 numberOrderBid) ][file-type frequency 8075 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8100 numberOrderBid > 0) [file-type (-1 * frequency 8100 numberOrderBid) ][file-type frequency 8100 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8125 numberOrderBid > 0) [file-type (-1 * frequency 8125 numberOrderBid) ][file-type frequency 8125 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8150 numberOrderBid > 0) [file-type (-1 * frequency 8150 numberOrderBid) ][file-type frequency 8150 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8175 numberOrderBid > 0) [file-type (-1 * frequency 8175 numberOrderBid) ][file-type frequency 8175 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8200 numberOrderBid > 0) [file-type (-1 * frequency 8200 numberOrderBid) ][file-type frequency 8200 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8225 numberOrderBid > 0) [file-type (-1 * frequency 8225 numberOrderBid) ][file-type frequency 8225 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8250 numberOrderBid > 0) [file-type (-1 * frequency 8250 numberOrderBid) ][file-type frequency 8250 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8275 numberOrderBid > 0) [file-type (-1 * frequency 8275 numberOrderBid) ][file-type frequency 8275 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8300 numberOrderBid > 0) [file-type (-1 * frequency 8300 numberOrderBid) ][file-type frequency 8300 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8325 numberOrderBid > 0) [file-type (-1 * frequency 8325 numberOrderBid) ][file-type frequency 8325 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8350 numberOrderBid > 0) [file-type (-1 * frequency 8350 numberOrderBid) ][file-type frequency 8350 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8375 numberOrderBid > 0) [file-type (-1 * frequency 8375 numberOrderBid) ][file-type frequency 8375 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8400 numberOrderBid > 0) [file-type (-1 * frequency 8400 numberOrderBid) ][file-type frequency 8400 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8425 numberOrderBid > 0) [file-type (-1 * frequency 8425 numberOrderBid) ][file-type frequency 8425 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8450 numberOrderBid > 0) [file-type (-1 * frequency 8450 numberOrderBid) ][file-type frequency 8450 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8475 numberOrderBid > 0) [file-type (-1 * frequency 8475 numberOrderBid) ][file-type frequency 8475 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8500 numberOrderBid > 0) [file-type (-1 * frequency 8500 numberOrderBid) ][file-type frequency 8500 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8525 numberOrderBid > 0) [file-type (-1 * frequency 8525 numberOrderBid) ][file-type frequency 8525 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8550 numberOrderBid > 0) [file-type (-1 * frequency 8550 numberOrderBid) ][file-type frequency 8550 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8575 numberOrderBid > 0) [file-type (-1 * frequency 8575 numberOrderBid) ][file-type frequency 8575 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8600 numberOrderBid > 0) [file-type (-1 * frequency 8600 numberOrderBid) ][file-type frequency 8600 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8625 numberOrderBid > 0) [file-type (-1 * frequency 8625 numberOrderBid) ][file-type frequency 8625 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8650 numberOrderBid > 0) [file-type (-1 * frequency 8650 numberOrderBid) ][file-type frequency 8650 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8675 numberOrderBid > 0) [file-type (-1 * frequency 8675 numberOrderBid) ][file-type frequency 8675 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8700 numberOrderBid > 0) [file-type (-1 * frequency 8700 numberOrderBid) ][file-type frequency 8700 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8725 numberOrderBid > 0) [file-type (-1 * frequency 8725 numberOrderBid) ][file-type frequency 8725 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8750 numberOrderBid > 0) [file-type (-1 * frequency 8750 numberOrderBid) ][file-type frequency 8750 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8775 numberOrderBid > 0) [file-type (-1 * frequency 8775 numberOrderBid) ][file-type frequency 8775 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8800 numberOrderBid > 0) [file-type (-1 * frequency 8800 numberOrderBid) ][file-type frequency 8800 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8825 numberOrderBid > 0) [file-type (-1 * frequency 8825 numberOrderBid) ][file-type frequency 8825 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8850 numberOrderBid > 0) [file-type (-1 * frequency 8850 numberOrderBid) ][file-type frequency 8850 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8875 numberOrderBid > 0) [file-type (-1 * frequency 8875 numberOrderBid) ][file-type frequency 8875 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8900 numberOrderBid > 0) [file-type (-1 * frequency 8900 numberOrderBid) ][file-type frequency 8900 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8925 numberOrderBid > 0) [file-type (-1 * frequency 8925 numberOrderBid) ][file-type frequency 8925 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8950 numberOrderBid > 0) [file-type (-1 * frequency 8950 numberOrderBid) ][file-type frequency 8950 numberOrderAsk]
  file-type ", "
  ifelse (frequency 8975 numberOrderBid > 0) [file-type (-1 * frequency 8975 numberOrderBid) ][file-type frequency 8975 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9000 numberOrderBid > 0) [file-type (-1 * frequency 9000 numberOrderBid) ][file-type frequency 9000 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9025 numberOrderBid > 0) [file-type (-1 * frequency 9025 numberOrderBid) ][file-type frequency 9025 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9050 numberOrderBid > 0) [file-type (-1 * frequency 9050 numberOrderBid) ][file-type frequency 9050 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9075 numberOrderBid > 0) [file-type (-1 * frequency 9075 numberOrderBid) ][file-type frequency 9075 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9100 numberOrderBid > 0) [file-type (-1 * frequency 9100 numberOrderBid) ][file-type frequency 9100 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9125 numberOrderBid > 0) [file-type (-1 * frequency 9125 numberOrderBid) ][file-type frequency 9125 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9150 numberOrderBid > 0) [file-type (-1 * frequency 9150 numberOrderBid) ][file-type frequency 9150 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9175 numberOrderBid > 0) [file-type (-1 * frequency 9175 numberOrderBid) ][file-type frequency 9175 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9200 numberOrderBid > 0) [file-type (-1 * frequency 9200 numberOrderBid) ][file-type frequency 9200 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9225 numberOrderBid > 0) [file-type (-1 * frequency 9225 numberOrderBid) ][file-type frequency 9225 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9250 numberOrderBid > 0) [file-type (-1 * frequency 9250 numberOrderBid) ][file-type frequency 9250 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9275 numberOrderBid > 0) [file-type (-1 * frequency 9275 numberOrderBid) ][file-type frequency 9275 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9300 numberOrderBid > 0) [file-type (-1 * frequency 9300 numberOrderBid) ][file-type frequency 9300 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9325 numberOrderBid > 0) [file-type (-1 * frequency 9325 numberOrderBid) ][file-type frequency 9325 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9350 numberOrderBid > 0) [file-type (-1 * frequency 9350 numberOrderBid) ][file-type frequency 9350 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9375 numberOrderBid > 0) [file-type (-1 * frequency 9375 numberOrderBid) ][file-type frequency 9375 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9400 numberOrderBid > 0) [file-type (-1 * frequency 9400 numberOrderBid) ][file-type frequency 9400 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9425 numberOrderBid > 0) [file-type (-1 * frequency 9425 numberOrderBid) ][file-type frequency 9425 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9450 numberOrderBid > 0) [file-type (-1 * frequency 9450 numberOrderBid) ][file-type frequency 9450 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9475 numberOrderBid > 0) [file-type (-1 * frequency 9475 numberOrderBid) ][file-type frequency 9475 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9500 numberOrderBid > 0) [file-type (-1 * frequency 9500 numberOrderBid) ][file-type frequency 9500 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9525 numberOrderBid > 0) [file-type (-1 * frequency 9525 numberOrderBid) ][file-type frequency 9525 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9550 numberOrderBid > 0) [file-type (-1 * frequency 9550 numberOrderBid) ][file-type frequency 9550 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9575 numberOrderBid > 0) [file-type (-1 * frequency 9575 numberOrderBid) ][file-type frequency 9575 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9600 numberOrderBid > 0) [file-type (-1 * frequency 9600 numberOrderBid) ][file-type frequency 9600 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9625 numberOrderBid > 0) [file-type (-1 * frequency 9625 numberOrderBid) ][file-type frequency 9625 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9650 numberOrderBid > 0) [file-type (-1 * frequency 9650 numberOrderBid) ][file-type frequency 9650 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9675 numberOrderBid > 0) [file-type (-1 * frequency 9675 numberOrderBid) ][file-type frequency 9675 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9700 numberOrderBid > 0) [file-type (-1 * frequency 9700 numberOrderBid) ][file-type frequency 9700 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9725 numberOrderBid > 0) [file-type (-1 * frequency 9725 numberOrderBid) ][file-type frequency 9725 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9750 numberOrderBid > 0) [file-type (-1 * frequency 9750 numberOrderBid) ][file-type frequency 9750 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9775 numberOrderBid > 0) [file-type (-1 * frequency 9775 numberOrderBid) ][file-type frequency 9775 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9800 numberOrderBid > 0) [file-type (-1 * frequency 9800 numberOrderBid) ][file-type frequency 9800 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9825 numberOrderBid > 0) [file-type (-1 * frequency 9825 numberOrderBid) ][file-type frequency 9825 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9850 numberOrderBid > 0) [file-type (-1 * frequency 9850 numberOrderBid) ][file-type frequency 9850 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9875 numberOrderBid > 0) [file-type (-1 * frequency 9875 numberOrderBid) ][file-type frequency 9875 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9900 numberOrderBid > 0) [file-type (-1 * frequency 9900 numberOrderBid) ][file-type frequency 9900 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9925 numberOrderBid > 0) [file-type (-1 * frequency 9925 numberOrderBid) ][file-type frequency 9925 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9950 numberOrderBid > 0) [file-type (-1 * frequency 9950 numberOrderBid) ][file-type frequency 9950 numberOrderAsk]
  file-type ", "
  ifelse (frequency 9975 numberOrderBid > 0) [file-type (-1 * frequency 9975 numberOrderBid) ][file-type frequency 9975 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10000 numberOrderBid > 0) [file-type (-1 * frequency 10000 numberOrderBid) ][file-type frequency 10000 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10025 numberOrderBid > 0) [file-type (-1 * frequency 10025 numberOrderBid) ][file-type frequency 10025 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10050 numberOrderBid > 0) [file-type (-1 * frequency 10050 numberOrderBid) ][file-type frequency 10050 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10075 numberOrderBid > 0) [file-type (-1 * frequency 10075 numberOrderBid) ][file-type frequency 10075 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10100 numberOrderBid > 0) [file-type (-1 * frequency 10100 numberOrderBid) ][file-type frequency 10100 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10125 numberOrderBid > 0) [file-type (-1 * frequency 10125 numberOrderBid) ][file-type frequency 10125 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10150 numberOrderBid > 0) [file-type (-1 * frequency 10150 numberOrderBid) ][file-type frequency 10150 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10175 numberOrderBid > 0) [file-type (-1 * frequency 10175 numberOrderBid) ][file-type frequency 10175 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10200 numberOrderBid > 0) [file-type (-1 * frequency 10200 numberOrderBid) ][file-type frequency 10200 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10225 numberOrderBid > 0) [file-type (-1 * frequency 10225 numberOrderBid) ][file-type frequency 10225 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10250 numberOrderBid > 0) [file-type (-1 * frequency 10250 numberOrderBid) ][file-type frequency 10250 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10275 numberOrderBid > 0) [file-type (-1 * frequency 10275 numberOrderBid) ][file-type frequency 10275 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10300 numberOrderBid > 0) [file-type (-1 * frequency 10300 numberOrderBid) ][file-type frequency 10300 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10325 numberOrderBid > 0) [file-type (-1 * frequency 10325 numberOrderBid) ][file-type frequency 10325 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10350 numberOrderBid > 0) [file-type (-1 * frequency 10350 numberOrderBid) ][file-type frequency 10350 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10375 numberOrderBid > 0) [file-type (-1 * frequency 10375 numberOrderBid) ][file-type frequency 10375 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10400 numberOrderBid > 0) [file-type (-1 * frequency 10400 numberOrderBid) ][file-type frequency 10400 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10425 numberOrderBid > 0) [file-type (-1 * frequency 10425 numberOrderBid) ][file-type frequency 10425 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10450 numberOrderBid > 0) [file-type (-1 * frequency 10450 numberOrderBid) ][file-type frequency 10450 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10475 numberOrderBid > 0) [file-type (-1 * frequency 10475 numberOrderBid) ][file-type frequency 10475 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10500 numberOrderBid > 0) [file-type (-1 * frequency 10500 numberOrderBid) ][file-type frequency 10500 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10525 numberOrderBid > 0) [file-type (-1 * frequency 10525 numberOrderBid) ][file-type frequency 10525 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10550 numberOrderBid > 0) [file-type (-1 * frequency 10550 numberOrderBid) ][file-type frequency 10550 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10575 numberOrderBid > 0) [file-type (-1 * frequency 10575 numberOrderBid) ][file-type frequency 10575 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10600 numberOrderBid > 0) [file-type (-1 * frequency 10600 numberOrderBid) ][file-type frequency 10600 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10625 numberOrderBid > 0) [file-type (-1 * frequency 10625 numberOrderBid) ][file-type frequency 10625 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10650 numberOrderBid > 0) [file-type (-1 * frequency 10650 numberOrderBid) ][file-type frequency 10650 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10675 numberOrderBid > 0) [file-type (-1 * frequency 10675 numberOrderBid) ][file-type frequency 10675 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10700 numberOrderBid > 0) [file-type (-1 * frequency 10700 numberOrderBid) ][file-type frequency 10700 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10725 numberOrderBid > 0) [file-type (-1 * frequency 10725 numberOrderBid) ][file-type frequency 10725 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10750 numberOrderBid > 0) [file-type (-1 * frequency 10750 numberOrderBid) ][file-type frequency 10750 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10775 numberOrderBid > 0) [file-type (-1 * frequency 10775 numberOrderBid) ][file-type frequency 10775 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10800 numberOrderBid > 0) [file-type (-1 * frequency 10800 numberOrderBid) ][file-type frequency 10800 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10825 numberOrderBid > 0) [file-type (-1 * frequency 10825 numberOrderBid) ][file-type frequency 10825 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10850 numberOrderBid > 0) [file-type (-1 * frequency 10850 numberOrderBid) ][file-type frequency 10850 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10875 numberOrderBid > 0) [file-type (-1 * frequency 10875 numberOrderBid) ][file-type frequency 10875 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10900 numberOrderBid > 0) [file-type (-1 * frequency 10900 numberOrderBid) ][file-type frequency 10900 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10925 numberOrderBid > 0) [file-type (-1 * frequency 10925 numberOrderBid) ][file-type frequency 10925 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10950 numberOrderBid > 0) [file-type (-1 * frequency 10950 numberOrderBid) ][file-type frequency 10950 numberOrderAsk]
  file-type ", "
  ifelse (frequency 10975 numberOrderBid > 0) [file-type (-1 * frequency 10975 numberOrderBid) ][file-type frequency 10975 numberOrderAsk]
  file-print ", "
  file-close
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^




;==============================================================================
;==============================================================================
;==============================================================================
;================= PLOTTING HISTOGRAMS AND TIME SERIES ========================
;==============================================================================
;==============================================================================
;==============================================================================

;//////////////////////////////////////////////////////////////////////////////
to histoSetupTestBuy
  let lengthofList count orders with [OrderB/A = "Buy"]
  if lengthofList > 0 [
    ask orders with [OrderB/A = "Buy"] [
      repeat OrderQuantity [
        set numberOrderBid lput ((OrderPrice / 4 ) * 100) numberOrderBid
      ]
    ]
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to histoSetupTestSell
  let lengthofList count orders with [OrderB/A = "Sell"]
  if lengthofList > 0 [
    ask orders with [OrderB/A = "Sell"] [
      repeat OrderQuantity [
        set numberOrderAsk lput ((OrderPrice / 4 ) * 100) numberOrderAsk
      ]
    ]
  ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to my-setup-plots ;;initialize plots
  clear-all-plots
  setup-plot2
  setup-plot3
  if((ticks mod 10) = 0)[
    setup-plot4
  ]
  setup-plot5
  setup-plot6
  setup-plot7
  setup-plot8
  setup-plot9
  setup-plot10
  setup-plot11
  setup-plot12
  setup-plot13
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to setup-plot2
  set-current-plot "Distribution of Bid/Ask"
  set-plot-x-range ((price / 4) * 100 - 1000) ((price / 4 ) * 100 + 1000)
  set-histogram-num-bars 100
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to setup-plot3
  set-current-plot "Price"
  plot (price / 4)
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to setup-plot4
  set-current-plot "Volume"
  plot volume
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to setup-plot5
  set-current-plot "Volatility"
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to setup-plot6
  set-current-plot "Ten Minute Moving Average Price"
  plot currentMA
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to setup-plot7
  set-current-plot "Ten Minute Moving Average Volume"
  plot currentMAV
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to setup-plot8
  set-current-plot "Market Depth"
  plot currentMAV
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to setup-plot9
  set-current-plot "Bid-Ask Spread"
  set-plot-y-range 0 5
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to setup-plot10
  set-current-plot "Turnover Rate"
  plot 0
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

;//////////////////////////////////////////////////////////////////////////////
to setup-plot11
  set-current-plot "Averages Shared Owned"
  plot 0
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to setup-plot12
  set-current-plot "Average Profit-Loss"
  plot 0
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to setup-plot13
  set-current-plot "Daily Price"
  plot (price / 4)
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to do-plots

  set-current-plot "Distribution of Bid/Ask"
  set-plot-x-range ((price / 4) * 100 - 1000) ((price / 4 ) * 100 + 1000)
  plot-pen-reset
  set-plot-pen-mode 1
  let n2 numberOrderBid
  set-current-plot-pen "Bid"
  histogram n2
  set-histogram-num-bars 100
  let a2 numberOrderAsk
  set-current-plot-pen "Ask"
  histogram a2
  set-histogram-num-bars 100

  if(ticks > endBurninTime)
  [
    set-current-plot "Price Returns"
    plot-pen-reset
    set-plot-pen-mode 1
    set-plot-x-range -0.025 .025
    set-histogram-num-bars 51
    histogram priceReturns
  ]

  if(ticks > endBurninTime)
  [
    set-current-plot "Price"
    plot (price / 4)

      set-current-plot "Daily Price"
      plot (price / 4)
      set-plot-x-range (ticks - 6440) (ticks - endBurninTime)


    if((ticks mod 10) = 8)[
      set-current-plot "Volume"
      set-plot-pen-mode 1

      plot volume

      set totalVolume (totalVolume + volume)
    ]]

  if(ticks  > 1000)[
    if((ticks mod 10) = 8)[
     set volatility lput ((price / 4) ) volatility
     set pastPrices lput price pastPrices
     let lengthVola length volatility
     if(ticks  > endBurninTime)[
       let subVL sublist volatility (lengthVola - 29) lengthVola
       let avgVL mean subVL
       set movingAverage lput avgVL movingAverage
     ]
     set movingAverageV lput volume movingAverageV
     set currentPriceVol (currentPriceVol + 1)
     if (currentPriceVol > 1000)[set currentPriceVol 1000]
     set volume 0
    ]
  ]

  set currentVol 0
  if(ticks >= (endBurninTime + 600))[
    let lengthVol length volatility
    let subVol sublist volatility (lengthVol - 10) lengthVol
    let maxVol max subVol
    let minVol min subVol
    set currentVol ln (maxVol / minVol)
    if(((ticks - endBurninTime) mod 60) = 0)[
      set-current-plot "Volatility"
      let lPR length priceReturns
      plot (sqrt(abs (item (lPR - 1) priceReturns)) * 15.87)

    ]
  ]

  set-current-plot "Ten Minute Moving Average Price"
  if(ticks > endBurninTime)[
    let lengthMA length volatility
    let lengthMB length pastPrices
    let subMA sublist volatility (lengthMA - 29) lengthMA
    let subMB sublist pastPrices (lengthMB - 29) lengthMB
    let avgMA mean subMA
    set pastMA item 1 subMB
    set currentMA avgMA
    plot currentMA
  ]


  set-current-plot "Ten Minute Moving Average Volume"
  set currentMAV 2
  if(ticks >= endBurninTime)[
    let lengthMAV length movingAverageV
    let subMAV sublist movingAverageV (lengthMAV - 29) lengthMAV
    let avgMAV mean subMAV
    set currentMAV avgMAV
    plot currentMAV
  ]


  set-current-plot "Market Depth"
  set currentBQD 2
  set currentSQD 2
  if(ticks >= endBurninTime)[
    set-current-plot-pen "Bid"
    plot sum [OrderQuantity] of orders with [OrderB/A = "Buy"]
    set-current-plot-pen "Ask"
    plot sum [OrderQuantity] of orders with [OrderB/A = "Sell"]
  ]

  set-current-plot "Bid-Ask Spread"
  if(ticks >= endBurninTime)[
    ifelse ((currentOrderAsk - currentOrderBid) / 2 >= 0)[
      plot (currentOrderAsk - currentOrderBid) / 2
    ][
      plot 0
    ]
  ]

  set-current-plot "Turnover Rate"
  if(ticks >= endBurninTime)[
    plot (currentMAV / (sum [OrderQuantity] of orders with [OrderB/A = "Sell"] + 1))
  ]

  if(ticks >= endBurninTime)[
    if((ticks mod 10) = 9)[
      set-current-plot "Aggressive Trades"
      plot (aggressiveBid - aggressiveAsk)
    ]
  ]

  if(ticks >= endBurninTime)[
    set-current-plot "Averages Shared Owned"
    set-current-plot-pen "MM"
    plot MktMkr_avgShares
    set-current-plot-pen "Demander"
    plot LiqDem_avgShares
    set-current-plot-pen "Supplier"
    plot LiqSup_avgShares
    set-current-plot-pen "Forced"
    plot FrcSal_avgShares
    set-current-plot-pen "LiqBuyBkr"
    plot avgSharesBkrBuy
    set-current-plot-pen "LiqSellBkr"
    plot avgSharesBkrSel
  ]

  if(ticks >= endBurninTime)[
    set-current-plot "Average Profit-Loss"
    set-current-plot-pen "MM"
    plot MktMkr_accountValue
    set-current-plot-pen "Demander"
    plot LiqDem_accountValue
    set-current-plot-pen "Supplier"
    plot LiqSup_accountValue
    set-current-plot-pen "LiqBuyBkr"
    plot accountValueBkrBuy
    set-current-plot-pen "LiqSellBkr"
    plot accountValueBkrSel
  ]

end
;code by Mark Paddrik




;==============================================================================
;==============================================================================
;==============================================================================
;================ REPORTERS FOR VARIABLES AND MARKET STATS ====================
;==============================================================================
;==============================================================================
;==============================================================================

;//////////////////////////////////////////////////////////////////////////////
to-report volumeTraded
  report precision ((sum [totalBought + totalSold] of traders)) 0
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report volumeCanceled
  report precision ((sum [totalCanceled] of traders)) 0
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report day
  report (int (((ticks) / 60) + 9.5 - ((endBurninTime) / 60)) / 24 )
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report hour
  ifelse (int (((ticks ) / 60) + 9.5 - ((endBurninTime) / 60))) mod 24 > 12 [ report (int (((ticks) / 60) + 9.5 - ((endBurninTime) / 60)) mod 24) - 12
    ][
      ifelse (int (((ticks ) / 60) + 9.5 - ((endBurninTime) / 60)) mod 24 = 0)[
        report 12
        ][
        report int (((ticks ) / 60) + 9.5 - ((endBurninTime) / 60)) mod 24]
    ]
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report hourOutput
    report int (((ticks ) / 60) + 9.5 - ((endBurninTime) / 60))
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report minute
  report int(((((ticks ) / 60) + 9.5 - ((endBurninTime) / 60)) mod 1)* 60)
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report AMPM
    ifelse (int (((ticks) / 60) + 9.5 - ((endBurninTime) / 60))) mod 24 > 11 [ report "AM"
    ][
      report "PM"
    ]
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report occurrences [x the-list]
  report reduce
    [ifelse-value (?2 = x) [?1 + 1] [?1]] (fput 0 the-list)
end
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


;//////////////////////////////////////////////////////////////////////////////
to-report frequency [val thelist]
  report length filter [? = val] thelist
end
;code by Mark Paddrik
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^






;==============================================================================
;==============================================================================
;==============================================================================
;======================= USER INTERFACE CONFIGURATION =========================
;==============================================================================
;==============================================================================
;==============================================================================
@#$#@#$#@
GRAPHICS-WINDOW
534
759
945
1191
200
200
1.0
1
10
1
1
1
0
1
1
1
-200
200
-200
200
0
0
1
ticks
30.0

BUTTON
22
36
122
69
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

MONITOR
474
43
558
92
Price
(price / 4)
2
1
12

BUTTON
40
80
103
113
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
474
17
624
37
Market State
16
0.0
1

TEXTBOX
-17
308
1403
348
===============================================================================================================
16
0.0
1

SLIDER
791
83
981
116
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
792
203
982
236
#_MktMkr
#_MktMkr
0
10
5
1
1
NIL
HORIZONTAL

TEXTBOX
812
42
1895
72
Numbers of Traders                         Trader Order Duration(Mins)         Trader Order Arrival Rate(Mins)             Trader Order Size Multiplier               Idiosyncratic Characteristic
12
0.0
1

SLIDER
1017
84
1233
117
LiqDem_TradeLength
LiqDem_TradeLength
30
600
120
30
1
NIL
HORIZONTAL

TEXTBOX
985
92
1016
112
 ---->\n\n
11
0.0
1

TEXTBOX
989
199
1019
236
\n---->
11
0.0
1

PLOT
9
613
656
733
Price
Time (1 Min)
Price
0.0
10.0
95.0
105.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" ""

PLOT
9
732
656
852
Volume
Time (10 Min)
Qty
0.0
10.0
0.0
10.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" ""

PLOT
9
851
656
971
Volatility
Time (1 Hr)
NIL
0.0
10.0
0.0
0.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" ""

MONITOR
599
731
656
776
Volume
int (totalVolume)
17
1
11

MONITOR
597
851
656
896
Volatility
precision (sqrt(abs (item ((length priceReturns) - 1) priceReturns)) * 15.87) 4
17
1
11

MONITOR
599
613
656
658
Price
(price / 4)
17
1
11

PLOT
10
971
655
1091
Ten Minute Moving Average Price
Time (10 Min))
MA Price
0.0
10.0
98.0
102.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" ""

MONITOR
596
972
655
1017
MAP
precision currentMA  2
17
1
11

PLOT
10
1091
655
1211
Ten Minute Moving Average Volume
Time (1 Min)
NIL
0.0
10.0
0.0
5.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" ""

MONITOR
598
1092
655
1137
MAV
precision currentMAV 2
17
1
11

PLOT
655
733
1304
853
Market Depth
Time (1 Min)
Qty
0.0
10.0
0.0
10.0
true
true
"" ""
PENS
"Bid" 1.0 0 -16777216 true "" ""
"Ask" 1.0 0 -2674135 true "" ""

PLOT
655
613
1303
734
Bid-Ask Spread
Time (1 Min)
Spread Diff
0.0
10.0
0.0
5.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" ""

PLOT
655
852
1304
972
Turnover Rate
Time (1 Min)
Volume/Stock
0.0
10.0
0.0
0.01
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" ""

PLOT
655
1092
1306
1212
Price Returns
NIL
NIL
0.5
0.5
0.0
10.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" ""

TEXTBOX
591
587
741
607
Market Measures
16
0.0
1

SLIDER
1019
203
1236
236
MktMkr_TradeLength
MktMkr_TradeLength
0
60
30
10
1
NIL
HORIZONTAL

MONITOR
186
43
236
88
H
hour
17
1
11

MONITOR
236
43
286
88
M
minute
17
1
11

TEXTBOX
233
12
383
30
Clock
16
0.0
1

TEXTBOX
1312
315
1332
1737
||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n||\n
11
0.0
1

PLOT
655
972
1305
1092
Aggressive Trades
Time (10 Min)
Qty
0.0
10.0
-2.0
2.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" ""

TEXTBOX
-3
1349
1343
1384
==============================================================================================================
16
0.0
1

PLOT
291
134
760
302
Distribution of Bid/Ask
NIL
NIL
0.0
10.0
0.0
10.0
true
false
"" ""
PENS
"Bid" 1.0 0 -16777216 true "" ""
"Ask" 1.0 0 -2674135 true "" ""

MONITOR
584
74
660
119
Current Ask
(currentOrderAsk / 4)
2
1
11

MONITOR
379
70
457
115
Current Bid
(currentOrderBid / 4)
2
1
11

MONITOR
53
217
186
262
Current Order ID
ordernumber
0
1
11

MONITOR
53
262
185
307
Number of Active Orders
count orders
0
1
11

TEXTBOX
1178
124
1440
142
Liquidity Supplier Trader
14
0.0
1

TEXTBOX
1169
64
1384
87
Liquidity Demander Trader
14
0.0
1

MONITOR
288
43
345
88
AM/PM
AMPM
17
1
11

SLIDER
791
143
981
176
#_LiqSup
#_LiqSup
0
25
10
1
1
NIL
HORIZONTAL

SLIDER
1017
145
1235
178
LiqSup_TradeLength
LiqSup_TradeLength
0
1440
1020
60
1
NIL
HORIZONTAL

TEXTBOX
1336
489
1682
741
Liquidity Demands:\nDistribution of Order Size\nProbability of Buying vs Selling\nNumber of Agents\n\nMarket Maker: \nDistrabution uniform of buy and selling on offered liquidity\nFunction of liquidity(inventory, shape(uniform), E(Liquidity Suppler Arrival Rate)\nNumber of Agents\nThe Inventory Limits are a finction of Balance Sheet conditions\n\nLarge Liquidity Suppler:\nArival Rate\nNumber of Agents\nDecision to Buy at what Price Funaction?
11
0.0
1

SLIDER
1714
84
1941
117
ProbabilityBuyofLiqyuidityDemander
ProbabilityBuyofLiqyuidityDemander
0
100
49
1
1
NIL
HORIZONTAL

SLIDER
1243
145
1468
178
liquidity_Supplier_Arrival_Rate
liquidity_Supplier_Arrival_Rate
0
2880
1320
120
1
NIL
HORIZONTAL

SLIDER
1241
84
1458
117
liquidity_Demander_Arrival_Rate
liquidity_Demander_Arrival_Rate
0
1440
240
60
1
NIL
HORIZONTAL

SLIDER
1243
203
1461
236
market_Makers_Arrival_Rate
market_Makers_Arrival_Rate
0
120
10
5
1
NIL
HORIZONTAL

MONITOR
136
43
186
88
D
day
0
1
11

PLOT
9
363
652
573
Averages Shared Owned
Time (1 Min)
Shares
0.0
10.0
-10.0
10.0
true
true
"" ""
PENS
"MM" 1.0 0 -16777216 true "" ""
"Demander" 1.0 0 -2674135 true "" ""
"Supplier" 1.0 0 -13840069 true "" ""
"Forced" 1.0 0 -8630108 true "" ""
"LiqBuyBkr" 1.0 0 -13345367 true "" ""
"LiqSellBkr" 1.0 0 -2674135 true "" ""

TEXTBOX
574
329
724
349
Participant Measures
16
0.0
1

PLOT
652
363
1304
573
Average Profit-Loss
Time (1 Min)
$
0.0
10.0
-10.0
10.0
true
true
"" ""
PENS
"MM" 1.0 0 -16777216 true "" ""
"Demander" 1.0 0 -2674135 true "" ""
"Supplier" 1.0 0 -13840069 true "" ""
"LiqBuyBkr" 1.0 0 -13345367 true "" ""
"LiqSellBkr" 1.0 0 -2674135 true "" ""

SLIDER
1473
144
1704
177
liquiditySupplierOrderSizeMultipler
liquiditySupplierOrderSizeMultipler
1
25
4
1
1
NIL
HORIZONTAL

SLIDER
1471
84
1704
117
liquidityDemanderOrderSizeMultipler
liquidityDemanderOrderSizeMultipler
1
10
5
1
1
NIL
HORIZONTAL

SLIDER
1474
203
1707
236
marketMakerOrderSizeMultipler
marketMakerOrderSizeMultipler
1
5
1
1
1
NIL
HORIZONTAL

TEXTBOX
1524
745
1674
765
Forced Sell Trader
16
0.0
1

INPUTBOX
1359
786
1444
846
FrcSal_QuantSale
2
1
0
Number

INPUTBOX
1454
787
1577
847
PeriodtoStartExecution
7436
1
0
Number

INPUTBOX
1589
787
1711
847
PeriodtoEndExecution
7440
1
0
Number

MONITOR
1720
788
1853
833
Duration of Execution
PeriodtoEndExecution - PeriodtoStartExecution
17
1
11

SLIDER
1713
143
1940
176
PercentPriceChangetoOrderSizeMultiple
PercentPriceChangetoOrderSizeMultiple
0.25
5
1
0.25
1
NIL
HORIZONTAL

MONITOR
202
93
266
138
NIL
ticks
17
1
11

TEXTBOX
1356
767
1873
812
Quantity to Sell      Tick Start Selling             Tick End Selling       Number of Period to Sell
12
0.0
1

MONITOR
1187
1092
1249
1137
Mean
mean(priceReturns)
4
1
11

MONITOR
1249
1092
1306
1137
StdDev
standard-deviation(priceReturns)
4
1
11

PLOT
655
1211
1306
1331
Daily Price
NIL
NIL
0.0
10.0
0.0
10.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" ""

SLIDER
1716
203
1917
236
MarketMakerInventoryLimit
MarketMakerInventoryLimit
5
100
60
5
1
NIL
HORIZONTAL

SWITCH
122
143
230
176
DepthFile
DepthFile
1
1
-1000

SWITCH
65
177
173
210
AgentFile
AgentFile
0
1
-1000

TEXTBOX
988
138
1016
166
\n---->
11
0.0
1

TEXTBOX
1216
184
1366
204
Market Maker
14
0.0
1

TEXTBOX
1136
10
1454
36
Agent Stochastic Parameters
20
0.0
1

SWITCH
1356
334
1467
367
timeseries
timeseries
1
1
-1000

INPUTBOX
1719
333
1874
393
timeseriesvalue
0
1
0
Number

SLIDER
1472
263
1706
296
LiqBkr_OrderSizeMultiplier
LiqBkr_OrderSizeMultiplier
0
10
10
1
1
NIL
HORIZONTAL

TEXTBOX
1214
244
1364
262
Liquidity Broker
14
0.0
1

SLIDER
1019
262
1236
295
BkrBuy_Limit
BkrBuy_Limit
0
10000
10000
1
1
NIL
HORIZONTAL

SLIDER
1240
263
1457
296
BkrSel_Limit
BkrSel_Limit
0
10000
10000
1
1
NIL
HORIZONTAL

INPUTBOX
1541
371
1702
431
endBurninTime
2000
1
0
Number

@#$#@#$#@
## ## WHAT IS IT?

This is a model of traders (agents) trading in futures market (OFR Exchange), placing orders in to a limit order book. The agents are constrcuted using the methodology in Paddrik et al. (2012). The agents are meant to represent 3 trading participants with different liquidity objectives. The 3 classes of agents are of:

Liquidity Demander - placement of market orders on either side of the market and going often to market with the purpose to transact

Market Maker - competitive by taking the position of straddling both sides of the market, taking long and short positions on the asset and placing their best bid and ask one price tick apart

Liquidity Suppler - private view on price but is a passive order supplier and such that they participates when price moves away with best bid-ask.

The model is meant to provide a mechanism for examining questions of price impact and liquiudity during periods of crisis.

## ## HOW IT WORKS

At the model set up with a given number of each types of traders and the amount of time they will leave an order into the market, before canceling it. The model is then run and at every tick each agent is examined to see if they can place an order or cancel/modify an order. The agent trading strategies determine what prices and quntites each agent will decided top place depending on market variables (price, moving average, depth of order book, ratio of order book, volatility, ....). The distriutions that are used in this version of the model represent agent decisions are meant to mimic those of true participants but for privcy concerns have been randomly adjusted.

The market is set up as a 'Price-Time Priority' basis. The highest bid order and the lowest ask order consitutes the best market for the given futures contract.

    - If it is a buy order it is matched against sell orders sorted by their price            followed by creation time.
    - If it is a sell order it is matched against buy orders sorted by their price            followed by creation time.

Agent specfic code can be examined by looking at the include button under the code tab. This will all you to see the underlying algorithms and functions that agents contain. This structure is meant to allow new agents to be introduced to the model with ease.

## ## HOW TO USE IT

Pressing the SETUP button will clear all transcations and initialize the traders.
Pressing the GO button will start the trades. Once the GO button is selected the traders are given the opportunitiy to place orders into the market before it opens, to fill the order book.

The 'Number of Traders' section allows you to use a slider bar to input the number of trades of each time they would like to see in the Market. The 'Time Between New Orders' slider can be used to determine the length a order is left in the limit order book for each trader type.

The 'Audit Trail' switch when On produces an audit trail of data that can be used to reconstruct events that occur in the simulated market. This is meant to be a mechanisum for researcher to examine the impact of types for traders with in the order book. The audit trail is a csv file titled "Orderbook" and will be located in the same directory as the netlogo file.

The 'Depth File' switch when On produces a file that containsd the depths of the order book at various pirce ticks such that you can produce images of the events that occur in the simulated market order book. This is meant to be a mechanisum for researcher to examine the impact of types for traders with in the order book.

The 'Agent File' switch when On produces a file that containsd the quantity of shares that an agent has at any one period with in the model such that a researcher can track each agent position.

## ## CREDITS AND REFERENCES

Paddrik, M., Hayes, R., Todd, A., Yang, S., Scherer, W.  & Beling, P.  (2012).  An Agent-based Model of the E-Mini S&P 500 and the Flash Crash.  IEEE Computational Intelligence for Financial Engineering and Economics.

Paddrik, M., Hayes, R., Scherer, W.  & Beling, P.  (2014).  Effects of Limit Order Book Information Level on Market Stability Metrics.  OFR Working Paper Series.

Paddrik, M. & Bookstaber R. (2015).  An Agnet-based Model for for Crisis Liquidity Dynamics.  OFR Working Paper Series.



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

x
false
0
Polygon -7500403 true true 270 75 225 30 30 225 75 270
Polygon -7500403 true true 30 75 75 30 270 225 225 270

@#$#@#$#@
NetLogo 5.3.1
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
<experiments>
  <experiment name="experiment" repetitions="100" runMetricsEveryStep="false">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="10000"/>
    <metric>price</metric>
    <enumeratedValueSet variable="FrcSal_QuantSale">
      <value value="2"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="MarketMakerInventoryLimit">
      <value value="60"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="MktMkr_TradeLength">
      <value value="30"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="LiqDem_TradeLength">
      <value value="120"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="PercentPriceChangetoOrderSizeMultiple">
      <value value="1"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="timeseries">
      <value value="false"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="#_LiqSup">
      <value value="10"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="#_LiqDem">
      <value value="100"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="#_MktMkr">
      <value value="5"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="LiqSup_TradeLength">
      <value value="1020"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="ProbabilityBuyofLiqyuidityDemander">
      <value value="49"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="liquidityDemanderOrderSizeMultipler">
      <value value="5"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="market_Makers_Arrival_Rate">
      <value value="10"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="PeriodtoStartExecution">
      <value value="7436"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="PeriodtoEndExecution">
      <value value="7440"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="timeseriesvalue">
      <value value="0"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="AgentFile">
      <value value="false"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="DepthFile">
      <value value="false"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="liquidity_Supplier_Arrival_Rate">
      <value value="1320"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="liquiditySupplierOrderSizeMultipler">
      <value value="4"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="marketMakerOrderSizeMultipler">
      <value value="1"/>
    </enumeratedValueSet>
    <enumeratedValueSet variable="liquidity_Demander_Arrival_Rate">
      <value value="240"/>
    </enumeratedValueSet>
  </experiment>
</experiments>
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
