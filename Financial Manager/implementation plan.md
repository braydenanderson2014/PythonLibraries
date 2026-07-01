* Excel: When a month has an override, use the override amount for the amount due instead of the normal amount due. that way everything is accurate.
* Unified DB for everything instead of separate DB's.
* Financial system: Excel... Need to be able to read an excel sheet.{
    A Column: Item names/descriptions
    B Column: Item numbers (Less important)
    C Column: Price
    D Column: QTY
    E Column: Discounts
    F Column: Markups (% and $ amounts supported)
    G COlumn: Total prices
    ----
    H26 "Payment Totals
    I26 the total amount of money in payments
    ----
    H27 "Tax%"
    I27 tax percentage
    ----
    H28 "Markup Amounts"
    I28 $ amount of all the markups summed together.
    ----
    H29 "Subtotal"
    I29 subtotal of all Total prices (G2:G250) summed together
    ----
    H30 "Discounts:"
    I30 Sum of all discounts added together
    ----
    H31 "Taxes:"
    I31 Tax $ amount based off of subtotal (skipping non taxable items like payments and labor etc.)
    ----
    H32 "Total:"
    I32 Total $ amount owed
    ----
    H33 "Status"
    I33 Paid in full, partially paid, etc
}