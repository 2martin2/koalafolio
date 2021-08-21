# -*- coding: utf-8 -*-
"""
Created on Fri Aug 24 09:44:38 2018

@author: Martin
"""
import openpyxl
import koalafolio.PcpCore.settings as settings
import datetime
import pytz
from dateutil.relativedelta import relativedelta
import koalafolio.PcpCore.core as core
import re
import koalafolio.gui.QLogger as logger

localLogger = logger.globalLogger

from openpyxl.styles import PatternFill, Alignment, Font

# %% create excelfile
def createProfitExcel(coinList, path, minDate, maxDate, currency='EUR', taxyearlimit=1,
                      includeTaxFreeTrades = True, lang="en", translator=None):

    if translator:
        def trans(text):
            return translator.translate(text, lang)

    wb = openpyxl.Workbook(write_only=False)
    wb.remove(wb.active)

    # %% profit sheets
    profitSumColumn = 'O'
    profitSumRows = []
    profitSumColumns = []
    for coinWallets in coinList.coins:
        # check if coin is report Currency
        if not coinWallets.isReportCurrency():
            # check if there are sells in the given timeframe
            validSellFound = False
            for coin in coinWallets.wallets:
                for sell in coin.tradeMatcher.sellsMatched:
                    if sell.date >= minDate and sell.date <= maxDate:
                        validSellFound = True
                        break
                if validSellFound:
                    tabname = coin.getWalletName()
                    wsname = re.sub('[^A-Za-z0-9_]+', '', tabname)
                    ws = wb.create_sheet(wsname)

                    # write top header
                    # cell = WriteOnlyCell(ws)
                    if translator:
                        ws.append(['', '', '', trans('Buy'), '', '', '', '', trans('Sell'), '', '', '', '', trans('Profit'), ''])
                    else:
                        ws.append(['', '', '', 'Ankauf', '', '', '', '', 'Verkauf', '', '', '', '', 'Profit', ''])
                    ws.merge_cells('A1:B1')
                    ws.merge_cells('D1:G1')
                    ws.merge_cells('I1:L1')
                    ws.merge_cells('N1:O1')
                    headingFont = Font(size=12, bold=True)
                    headingAlignment = Alignment(horizontal='center',
                                                 vertical='center')
                    headings = [ws['A1'], ws['D1'], ws['I1'], ws['N1']]
                    for heading in headings:
                        heading.font = headingFont
                        heading.alignment = headingAlignment

                    # blue, green, yellow, purple
                    headingColors = ['FF61D2FF', 'FF6DE992', 'FFFFFF52', 'FFE057FF']
                    for i in range(len(headings)):
                        headings[i].fill = PatternFill(fill_type='solid',
                                                       start_color=headingColors[i],
                                                       end_color=headingColors[i])

                    # empty row
                    ws.append([])

                    # write sub header
                    if translator:
                        ws.append(
                            ['', '', '', trans('Date'), trans('Amount'), trans('Price'), trans('Value'), '', trans('Date'),
                             trans('Amount'), trans('Price'), trans('Value'), '', trans('Profit'), trans('tax relevant')])
                        ws.append(['', '', '', '', trans('in') + ' ' + trans('pc'),
                                   trans('in') + ' ' + currency + '/' + trans('pc'),
                                   trans('in') + ' ' + currency, '', '', trans('in') + ' ' + trans('pc'),
                                   trans('in') + ' ' + currency + '/' + trans('pc'), trans('in') + ' ' + currency, '',
                                   trans('in') + ' ' + currency, trans('in') + ' ' + currency])
                    else:
                        ws.append(['', '', '', 'Datum', 'Anzahl', 'Preis', 'Wert', '', 'Datum', 'Anzahl', 'Preis', 'Wert', '',
                                   'Gewinn', 'zu versteuern'])
                        ws.append(['', '', '', '', 'in Stk', 'in ' + currency + '/Stk', 'in ' + currency, '', '', 'in Stk',
                                   'in ' + currency + '/Stk', 'in ' + currency, '', 'in ' + currency, 'in ' + currency])

                    # coinname
                    ws.append([coin.coinname, ''])

                    firstProfitRow = ws.max_row + 1
                    # write data
                    for irow in range(len(coin.tradeMatcher.profitMatched)):
                        sell = coin.tradeMatcher.sellsMatched[irow]
                        # check date of sell
                        if sell.date >= minDate and sell.date <= maxDate:
                            buy = coin.tradeMatcher.buysMatched[irow]
                            profit = coin.tradeMatcher.profitMatched[irow]
                            # if taxyearlimit is given # if limit is relevant
                            if taxyearlimit and ((sell.date - relativedelta(years=taxyearlimit)) > buy.date):  # if taxyearlimit is given
                                taxProfit = 0
                                if includeTaxFreeTrades:
                                    ws.append(
                                        ['', '', '', buy.date, buy.amount, buy.getPrice()[currency],
                                         buy.value[currency], '', sell.date, sell.amount, sell.getPrice()[currency],
                                         sell.value[currency], '', round(profit[currency], 3), round(taxProfit, 3)])
                            else:
                                taxProfit = profit[currency]
                                ws.append(['', '', '', buy.date, buy.amount, buy.getPrice()[currency],
                                           buy.value[currency], '', sell.date, sell.amount, sell.getPrice()[currency],
                                           sell.value[currency], '', round(profit[currency], 3), round(taxProfit, 3)])

                    profitSumRows.append(ws.max_row + 2)
                    profitSumColumns.append(15)
                    #                ws['M' + str(profitSumRows[-1])] = 'Summe'
                    ws[profitSumColumn + str(profitSumRows[-1])] = '=ROUNDDOWN(SUM(' + profitSumColumn + str(
                        firstProfitRow) + ':' + profitSumColumn + str(profitSumRows[-1] - 2) + '),2)'

                    # set width of date columns
                    ws.column_dimensions['D'].width = 11
                    ws.column_dimensions['I'].width = 11
                    # set width of gap columns
                    gapColumns = ['C', 'H', 'M', 'P']
                    gapFill = PatternFill(fill_type='solid',
                                          start_color='FFC8C8C8',
                                          end_color='FFC8C8C8')
                    for gapColumn in gapColumns:
                        ws.column_dimensions[gapColumn].width = 4

                        # set gap color
                        for cell in ws[gapColumn]:
                            cell.fill = gapFill

                    # page setup
                    #                ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
                    #                ws.page_setup.fitToWidth = 1
                    pageSetup(ws)

    # %% fee sheets
    feeSumColumn = 'G'
    feeSumRows = []
    for coin in coinList.coins:
        fees = coin.getFees()
        feeSum = core.CoinValue()
        for fee in fees:
            if fee.date.date() >= minDate and fee.date.date() <= maxDate:
                feeSum.add(fee.value)
        if feeSum[currency] != 0:  # if fees have been paid
            wsname = re.sub('[^A-Za-z0-9]+', '', coin.coinname)
            ws = wb.create_sheet(wsname + '_fees')

            # write top header
            # cell = WriteOnlyCell(ws)
            if translator:
                ws.append(['', '', '', trans('Fees'), '', '', '', ''])
            else:
                ws.append(['', '', '', 'Gebühren', '', '', '', ''])
            ws.merge_cells('A1:B1')
            ws.merge_cells('D1:G1')
            headingFont = Font(size=12, bold=True)
            headingAlignment = Alignment(horizontal='center',
                                         vertical='center')
            headings = [ws['A1'], ws['D1']]
            for heading in headings:
                heading.font = headingFont
                heading.alignment = headingAlignment

            # blue, purple
            headingColors = ['FF61D2FF', 'FFE057FF']
            for i in range(len(headings)):
                headings[i].fill = PatternFill(fill_type='solid',
                                               start_color=headingColors[i],
                                               end_color=headingColors[i])

            # empty row
            ws.append([])

            # write sub header
            if translator:
                ws.append(
                    ['', '', '', trans('Date'), trans('Fee'), '', trans('Fee'), ''])
                ws.append(['', '', '', '', trans('in') + ' ' + trans('pc'), '', trans('in') + ' ' + currency, ''])
            else:
                ws.append(
                    ['', '', '', 'Datum', 'Gebühr', '', 'Gebühr', ''])
                ws.append(['', '', '', '', 'in Stk', '', 'in ' + currency, ''])

            # coinname
            ws.append([coin.coinname, ''])

            firstProfitRow = ws.max_row + 1
            # write data
            for fee in coin.getFees():
                # check date of sell
                if fee.date.date() >= minDate and fee.date.date() <= maxDate:
                    feedate = fee.date.astimezone(pytz.utc).replace(tzinfo=None)
                    ws.append(['', '', '', feedate, fee.amount, '', round(fee.value[currency], 3), ''])

            profitSumRows.append(ws.max_row + 2)
            profitSumColumns.append(7)
            #                ws['M' + str(profitSumRows[-1])] = 'Summe'
            ws[feeSumColumn + str(profitSumRows[-1])] = '=ROUNDDOWN(SUM(' + feeSumColumn + str(
                firstProfitRow) + ':' + feeSumColumn + str(profitSumRows[-1] - 2) + '),2)'

            # set width of date columns
            ws.column_dimensions['D'].width = 11
            # set width of gap columns
            gapColumns = ['C', 'H']
            gapFill = PatternFill(fill_type='solid',
                                  start_color='FFC8C8C8',
                                  end_color='FFC8C8C8')
            for gapColumn in gapColumns:
                ws.column_dimensions[gapColumn].width = 4

                # set gap color
                for cell in ws[gapColumn]:
                    cell.fill = gapFill

            # page setup
            #                ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
            #                ws.page_setup.fitToWidth = 1
            pageSetup(ws)

    # %% reward sheets
    rewardSumColumn = 'G'
    rewardSumRows = []
    for coin in coinList.coins:
        rewards = coin.getRewards()
        rewardSum = core.CoinValue()
        for reward in rewards:
            if reward.date.date() >= minDate and reward.date.date() <= maxDate:
                rewardSum.add(reward.value)
        if rewardSum[currency] != 0:  # if rewards have been received
            wsname = re.sub('[^A-Za-z0-9]+', '', coin.coinname)
            ws = wb.create_sheet(wsname + '_rewards')

            # write top header
            # cell = WriteOnlyCell(ws)
            if translator:
                ws.append(['', '', '', trans('Rewards'), '', '', '', ''])
            else:
                ws.append(['', '', '', 'Gebühren', '', '', '', ''])
            ws.merge_cells('A1:B1')
            ws.merge_cells('D1:G1')
            headingFont = Font(size=12, bold=True)
            headingAlignment = Alignment(horizontal='center',
                                         vertical='center')
            headings = [ws['A1'], ws['D1']]
            for heading in headings:
                heading.font = headingFont
                heading.alignment = headingAlignment

            # blue, purple
            headingColors = ['FF61D2FF', 'FFE057FF']
            for i in range(len(headings)):
                headings[i].fill = PatternFill(fill_type='solid',
                                               start_color=headingColors[i],
                                               end_color=headingColors[i])

            # empty row
            ws.append([])

            # write sub header
            if translator:
                ws.append(
                    ['', '', '', trans('Date'), trans('Reward'), '', trans('Reward'), ''])
                ws.append(['', '', '', '', trans('in') + ' ' + trans('pc'), '', trans('in') + ' ' + currency, ''])
            else:
                ws.append(
                    ['', '', '', 'Datum', 'Gebühr', '', 'Gebühr', ''])
                ws.append(['', '', '', '', 'in Stk', '', 'in ' + currency, ''])

            # coinname
            ws.append([coin.coinname, ''])

            firstProfitRow = ws.max_row + 1
            # write data
            for reward in coin.getRewards():
                # check date of sell
                if reward.date.date() >= minDate and reward.date.date() <= maxDate:
                    rewarddate = reward.date.astimezone(pytz.utc).replace(tzinfo=None)
                    ws.append(['', '', '', rewarddate, reward.amount, '', round(reward.value[currency], 3), ''])

            profitSumRows.append(ws.max_row + 2)
            profitSumColumns.append(7)
            #                ws['M' + str(profitSumRows[-1])] = 'Summe'
            ws[rewardSumColumn + str(profitSumRows[-1])] = '=ROUNDDOWN(SUM(' + rewardSumColumn + str(
                firstProfitRow) + ':' + rewardSumColumn + str(profitSumRows[-1] - 2) + '),2)'

            # set width of date columns
            ws.column_dimensions['D'].width = 11
            # set width of gap columns
            gapColumns = ['C', 'H']
            gapFill = PatternFill(fill_type='solid',
                                  start_color='FFC8C8C8',
                                  end_color='FFC8C8C8')
            for gapColumn in gapColumns:
                ws.column_dimensions[gapColumn].width = 4

                # set gap color
                for cell in ws[gapColumn]:
                    cell.fill = gapFill

            # page setup
            #                ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
            #                ws.page_setup.fitToWidth = 1
            pageSetup(ws)

    # %% overview sheet
    ws = wb.create_sheet('Overview', 0)

    # write top header
    if translator:
        ws.append(['', '', '', trans('Profit'), '', ''])
    else:
        ws.append(['', '', '', 'Profit', '', ''])
    ws.merge_cells('A1:B1')
    ws.merge_cells('D1:E1')
    headingFont = Font(size=12, bold=True)
    headingAlignment = Alignment(horizontal='center',
                                 vertical='center')

    # blue, purple
    headings = [ws['A1'], ws['D1']]
    for heading in headings:
        heading.font = headingFont
        heading.alignment = headingAlignment

    headingColors = ['FF61D2FF', 'FFE057FF']
    for i in range(len(headings)):
        headings[i].fill = PatternFill(fill_type='solid',
                                       start_color=headingColors[i],
                                       end_color=headingColors[i])

    # empty row
    ws.append([])

    # write sub header
    if translator:
        ws.append(['', '', '', trans('Group'), trans('Profit'), ''])
        ws.append(['', '', '', '', trans('in') + ' ' + currency, ''])
        ws.append([trans('Timeframe'), str(minDate) + ' : ' + str(maxDate)])
    else:
        ws.append(['', '', '', 'Gruppe', 'Gewinn', ''])
        ws.append(['', '', '', '', 'in ' + currency, ''])
        ws.append(['Zeitraum', str(minDate) + ' : ' + str(maxDate)])

    firstProfitRow = ws.max_row + 1

    # write data
    sheets = wb.sheetnames[1:]
    for isheet in range(len(sheets)):
        #            profit = wb[sheets[isheet]][profitSumColumn + str(profitSumRows[isheet])].value
        #            =INDIREKT("ETH!"&ADRESSE(13;16;4))
        profit = '=INDIRECT(\"' + sheets[isheet] + '!\"&ADDRESS(' + str(profitSumRows[isheet]) + ',' + str(profitSumColumns[isheet]) + ',4))'
        ws.append(['', '', '', sheets[isheet], profit])

    profitSumRow = ws.max_row + 2
    profitSumColumn = 'E'
    #                ws['M' + str(profitSumRows[-1])] = 'Summe'
    ws[profitSumColumn + str(profitSumRow)] = '=SUM(' + profitSumColumn + str(
        firstProfitRow) + ':' + profitSumColumn + str(profitSumRow - 2) + ')'

    # set width of gap columns
    gapColumns = ['C', 'F']
    gapFill = PatternFill(fill_type='solid',
                          start_color='FFC8C8C8',
                          end_color='FFC8C8C8')
    for gapColumn in gapColumns:
        ws.column_dimensions[gapColumn].width = 4

        # set gap color
        for cell in ws[gapColumn]:
            cell.fill = gapFill

    # page setup
    pageSetup(ws)

    def textLen(value):
        if value is None:
            return 5
        elif isinstance(value, float):
            #            return len(str(value))/2
            return 5
        elif isinstance(value, str) and '=' in value:
            return 10
        else:
            length = len(str(value)) + 2
            if length < 5:
                length = 5
            return length

    for ws in wb:
        for column_cells in ws.columns:
                length = max(textLen(cell.value) for cell in column_cells[1:])
                ws.column_dimensions[str(column_cells[1].column_letter)].width = length


    # save file
    # wb.save(path + '-' + str(datetime.datetime.now()).replace(' ', '_').replace(':', '_').replace('-', '_').replace('.',
    #                                                                                                                 '_') + '.xlsx')
    try:
        wb.save(path)
    except PermissionError as ex:
        localLogger.error("saving export failed: " + str(ex))


def pageSetup(ws):
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.fitToWidth = 1



