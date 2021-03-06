import pymysql
import datetime
from datetime import timedelta
import utils
from pprint import pprint

class TradeLog:
    db = None
    positions = ['long', 'short']
    accounts = ['tos', 'ibg', 'ibc']
    table_trades = 'trades'
    table_rules = 'trade_rules'
    table_lessons = 'trade_lessons'
    table_actions = 'actions'
    table_watchlist = 'watchlist'
    table_ideas = 'trade_ideas'
    table_reasons = 'trade_reasons'
    table_plan = 'trade_plan'
    MAX_LOSS = 10

    def __init__(self):
        try:
            self.db = pymysql.connect(host = 'localhost', port = 3306, user = 'root', passwd = '', db = 'trade_log')
        except Exception as e:
            print('Unable to connect to DB\n' + str(e))
            utils.exit_app()

    def menu(self):
        utils.title('Menu')
        q = "SELECT * FROM menu"
        menu = self.run_query(q)
        for item in menu:
            print('{0:<3} {1:<2}'.format(str(item[0]) + '.', item[1]))

    def show_rules(self):
        utils.title('Trading Rules')
        with self.db.cursor() as cur:
            cur.execute("SELECT rule FROM " + self.table_rules + " ORDER BY RAND()")
            counter = 1
            print('Press ENTER to continue viewing each trading rule & "q" to quit\n')
            for row in cur.fetchall():
                print(str(counter) + ' - ' + row[0])
                counter += 1
                q = input()
                if q == 'q':
                    break
               
            cur.close()

        #get last viewed
        with self.db.cursor() as cur:
            cur.execute("SELECT viewed_rules FROM " + self.table_actions + " ORDER BY viewed_rules DESC LIMIT 1")
            last_viewed = cur.fetchone()
            if last_viewed != None:
                d_converted = ''
                for i, d in enumerate(last_viewed):
                    if i == len(last_viewed) -1:
                        d_converted += str(d)
                    else:
                        d_converted += str(d) + '-'

                print('Last viewed trade rules on: ' + d_converted)
                last_date = datetime.datetime.strptime(d_converted, '%Y-%m-%d').date()
            else:
                compare_last_date = False
                
            cur.close()

        #update last viewed date to present
        date = datetime.date.today()
        if last_date != False and date > last_date:
            with self.db.cursor() as cur:
                cur.execute("INSERT INTO " + self.table_actions + " (viewed_rules) VALUES (%s)", (date))
                self.db.commit()
                cur.close()

        print('Total Rules: ' + str(counter - 1))

    def show_lessons(self):
        utils.title('Trading Lessons Learned')
        q = "SELECT lesson FROM " + self.table_lessons + " ORDER BY RAND()"
        counter = 1
        print('Press ENTER to continue viewing each trading lesson & "q" to quit\n')
        rows = self.run_query(q)
        for row in rows:
            print(str(counter) + ' - ' + row[0])
            counter += 1
            q = input()
            if q == 'q':
                break

    def check_last_rules_viewed(self):
        today = datetime.date.today()
        query = "SELECT viewed_rules FROM " + self.table_actions + " ORDER BY viewed_rules DESC LIMIT 1"
        row = self.run_query(query, True)
        if row != False:
            diff = (today - row[0]).days
            if diff >= 7:
                print('\nWARNING: It has been ' + str(diff) + ' days since viewing trading rules\n')

    def check_expirations(self):
        today = datetime.date.today()
        to_show = []
        query = "SELECT symbol, exp_date FROM " + self.table_trades + " WHERE status = 'open' AND exp_date > '0000-00-00'"
        rows = self.run_query(query)
        if rows != False:
            for row in rows:
                if (today - row[1]).days >= -7:
                    to_show.append({'symbol': row[0], 'exp': row[1]})

            if len(to_show) > 0:
                print('The following option trades are expiring soon:')
                for row in to_show:
                    print(row.get('symbol') + ' - ' + str(row.get('exp')))
                print()

    def check_exit_date_open(self):
        query = "SELECT id, symbol FROM " + self.table_trades + " WHERE status = 'open' AND exit_date > '0000-00-00'"
        rows = self.run_query(query)
        if rows != False:
            print('The following have not been closed properly:\n')
            for row in rows:
                print('ID : SYMBOL: ' + str(row[0]) + ' : ' + row[1])

    def show_watchlist(self):
        utils.title('Watchlist')
        query = "SELECT ticker FROM " + self.table_watchlist + " ORDER BY ticker"
        rows = self.run_query(query)
        if rows != False:
            watchlist = ''
            total = 0
            for i, row in enumerate(rows):
                total += 1
                if i == 0:
                    watchlist += row[0] + ', '
                elif i == len(rows) - 1:
                    watchlist += row[0]
                elif i % 10 == 0:
                    watchlist += row[0] + '\n'
                else:
                    watchlist += row[0] + ', '

            print(watchlist)
            print('\nTotal watchlist items: ' + str(total))
        else:
            print('None found')

    def show_trade_plan(self):
        utils.title('Trade ideas')
        begin_week = datetime.date.today() - datetime.timedelta(days = datetime.date.today().isoweekday() % 7)
        query = "SELECT ticker, notes, idea_date FROM " + self.table_ideas + " WHERE idea_date >= '" + str(begin_week) + "' ORDER BY idea_date DESC"
        rows = self.run_query(query)
        if rows != False:
            to_show = ''
            for row in rows:
                to_show += str(row[2]) + ' - ' + row[0] + ' - ' + row[1] + '\n'

            print(to_show)
        else:
            print('None')

    def trade_entry(self):
        utils.title('Trade Entry')

        print('Enter the symbol, entry price, position, date, and account:\n(comma separated):\n')

        values = input()

        if values != '':
            result = utils.split_string(values)
            if len(result) == 5:
                symbol = result[0]
                entry_price = result[1]
                position = result[2]
                trade_date = result[3]
                account = result[4]
                
                errors = []
                position = position.lower()
                symbol = symbol.upper()
                account = account.lower()

                if len(symbol) > 8 or len(symbol) == 0:
                    errors.append('Symbol cannot be empty or greater than 5')
                if not utils.validate_float(entry_price):
                    errors.append('Entry price not a valid float value')
                if not position in self.positions:
                    errors.append('Position can only be long or short')
                if not utils.validate_date(trade_date):
                    errors.append('Invalid trade date entered')
                if not account in self.accounts:
                    errors.append('Account not valid')

                if len(errors) > 0:
                    for x in errors:
                        print(x)
                else:
                    query = "INSERT INTO " + self.table_trades + " (symbol, entry, position, entry_date, account) VALUES (%s, %s, %s, %s, %s)"
                    try:
                        cur = self.db.cursor()
                        cur.execute(query, (symbol, entry_price, position, trade_date, account))
                        db.commit()
                        cur.close()
                        print('Trade successfully inserted')
                    except ValueError:
                        print('Problem inserting trade')

            else:
                print('5 values must be entered for a new trade')
        else:
            print('Nothing entered')

    def add_idea(self):
        utils.title('Add Trade Idea')

        print('Enter symbol & notes (comma separated):\n')

        values = input()

        if values != '':
            result = utils.split_string(values)
            if len(result) == 2:
                symbol = result[0]
                notes = result[1]

                symbol = symbol.upper()
                date = datetime.date.today()
                errors = []

                if len(symbol) > 8 or len(symbol) == 0:
                    errors.append('Symbol cannot be greater than 8 or empty') 
                if len(notes) > 255 or len(notes) == 0:
                    errors.append('Notes cannot be greater than 255 or empty')

                if len(errors) > 0:
                    for x in errors:
                        print(x)
                else:
                    query = "INSERT INTO " + self.table_ideas + " (ticker, notes, idea_date) VALUES (%s, %s, %s)"
                    try:
                        cur = self.db.cursor()
                        cur.execute(query, (symbol, notes, date))
                        self.db.commit()
                        cur.close()
                        print('Trade idea successfully added')
                    except ValueError:
                        print('Problem inserting trade idea')
            else:
                print('2 values must be entered for new trade idea')
        else:
            print('Nothing entered')

    def view_trades(self, month = False, year = False, day = False, o = False, m_opt = False, a = False):
        today = datetime.datetime.today()
        now_yr = today.year
        break_rule_stops = 0
        if month == False:
            month = today.month
        to_d = 1
        if day != False:
            to_d = day

        title = 'Viewing closed trades' if o == False else 'Viewing current open trades'

        utils.title(title)

        if year == False:
            print('Month Start: ' + utils.get_month(month) + '\n')
        else:
            print('Month Start: ' + utils.get_month(month) + ' ' + str(year) + '\n')

        if m_opt == False:
            to_m = month
            to_y = year
        else:
            if m_opt == 'y':
                if month != 12:
                    to_m = month + 1
                    to_y = year
                else:
                    to_m = 1
                    to_y = year + 1
            else:
                to_m = month
                to_y = year
            
            if day == False:
                print('Viewing ' + utils.get_month(month) + ' only\n')
            else:
                print('Viewing ' + utils.get_month(month) + ' ' + str(to_d) + utils.day_ext(to_d) + ' only\n')

        if year == False or day == False:
            end = datetime.date.today().replace(month = to_m, day = to_d) - datetime.timedelta(days = 1)
        else:
            end = datetime.date.today().replace(month = to_m, day = to_d, year = to_y)

        if year == False:
            begin = datetime.date.today().replace(month = month, day = to_d)
        else:
            begin = datetime.date.today().replace(month = month, day = to_d, year = year)
        
        query = "SELECT * FROM " + self.table_trades

        if o == False:
            if day == False:
                query += " WHERE exit_date >= '" + str(begin) + "' AND status = 'closed'"
            else:
                query += " WHERE entry_date = '" + str(begin) + "' AND status = 'closed'"
            if m_opt == False:
                pass
            else:
                if day == False:
                    query += " AND exit_date <= '" + str(end) + "'"
                else:
                    query += " OR exit_date = '" + str(end) + "'"
        else:
            query += " WHERE status = 'open'"

        if a != False:
        	query += " AND account = '" + a + "'"

        if o == False:
        	query += " ORDER BY exit_date DESC"
        else:
        	query += " ORDER BY entry_date DESC"

        rows = self.run_query(query)
        if rows != False:
            if o == False:
                format_header = '{0:4} {1:<6} {2:<6} {3:<10} {4:<5} {5:<5} {6:<8} {7:<8} {8:<8}'.format('ID', 'SYMBOL', 'POS', 'EX:DATE', 'ACC', 'COM', 'RESULT', 'STATUS', 'EN:DATE')
            else:
                format_header = '{0:4} {1:<6} {2:<6} {3:<10} {4:<5} {5:<5} {6:<8} {7:<8} {8:<8} {9:<6} {10:<5}'.format('ID', 'SYMBOL', 'POS', 'EN:DATE', 'ACC', 'COM', 'RESULT', 'STATUS', 'EN:PRICE', 'STOP', 'OP:EXP')
            print(format_header)
            total_profit = total_loss = comm_g = comm_c = comm_t = total_comm = total_trades = 0
            positions, exits, results, statuses, accounts, symbols, t_results, g_results, b_results, loss_diff = [], [], [], [], [], [], [], [], [], []
            for row in rows:
                if row[13] > 0:
                    total_profit += row[13]
                else:
                    total_loss += row[13]
                    if row[13] < 0 and (row[1] == 'ES' or row[1] == 'MES'):
                        if row[2] > row[3]:
                            diff = row[2] - row[3]
                        else:
                            diff = row[3] - row[2]
                        if row[2] - row[5] > self.MAX_LOSS or row[5] - row[2] > self.MAX_LOSS:
                        	break_rule_stops += 1
                        
                        if diff > 0:
                            loss_diff.append(diff)

                if row[10] == 'ibg':
                    comm_g += row[11] + row[12]
                elif row[10] == 'ibc':
                    comm_c += row[11] + row[12]
                else:
                    comm_t += row[11] + row[12]

                comm = row[11] + row[12]
                positions.append(row[4])
                exits.append({'exit': row[14], 'status': row[17]})
                total_trades += 1
                results.append(row[13])
                statuses.append(row[17])
                accounts.append(row[10])
                symbols.append(row[1])
                if o == False:
                    if row[10] == 'tos':
                        t_results.append(row[13])   
                    elif row[10] == 'ibg':
                        g_results.append(row[13])
                    else:
                        b_results.append(row[13]) 

                if o == False:
                    print_row = '{0:<4d} {1:<6} {2:<6} {3:<10} {4:<5} {5:<5f} {6:<8f} {7:<8} {8:<8}'.format(row[0], row[1], row[4], str(row[8]), row[10], comm, row[13], row[17], str(row[7]))
                else:
                    print_row = '{0:<4d} {1:<6} {2:<6} {3:<8} {4:<5} {5:<5f} {6:<8f} {7:<8} {8:<8} {9:<6} {10:<5}'.format(row[0], row[1], row[4], str(row[7]), row[10], comm, row[13], row[17], utils.format_price(row[2]), utils.format_price(row[5]), str(row[18]))
                print(print_row)    

            total_comm = comm_g + comm_c + comm_t
            after_comm = (total_profit + total_loss) - total_comm
            pos_sum = utils.sum_positions(positions)
            exit_early = utils.sum_exit_early(exits)
            win_rate = utils.win_rate(results)
            status_sum = utils.sum_statuses(statuses)
            acc_sum = utils.sum_accounts(accounts)
            if o == False:
                acc_results = utils.account_results(t_results, g_results, b_results)
            print('{0:<22} {1:6}'.format('\nGross proft: ', '$' + str(total_profit)))
            print('{0:<21} {1:6}'.format('Gross loss: ', '$' + str(total_loss)))
            print('{0:<21} {1:6}'.format('Net proft/loss: ', '$' + str(total_profit + total_loss)))
            print('{0:<21} {1:6}'.format('Total commissions: ', '$' + str(total_comm)))     
            print('{0:<21} {1:6}'.format('Final net results: ', '$' + str(after_comm)))   
            if o == False and day == False:
                if month == today.month and now_yr == today.year:
                    open_locked = self.get_locked_open()
                    if open_locked > 0:
                        print('-------------')
                        print('{0:<21} {1:6}'.format('Total open locked: ', '$' + str(open_locked)))
                        print('{0:<21} {1:6}'.format('Total with open: ', '$' + str(after_comm + open_locked)))
            print('Note: commissions not exact')

            print('\nTotal trades: ' + str(total_trades))
            print('Total long: ' + str(pos_sum[0]) + ' Total short: ' + str(pos_sum[1]))
            print('Trades exited early: ' + str(exit_early[0]) + ' Good exits: ' + str(exit_early[1]))
            print('Wins: ' + str(win_rate[0]) + ' Losses: ' + str(win_rate[1]) + ' Breakeven: ' + str(win_rate[6]) + ' Win Rate: ' + str(round(win_rate[2], 2)) 
                + '%' + ' Average: $' + str(round(win_rate[3], 2)))
            minimum = '$' + str(win_rate[5]) if win_rate[5] < 0 else 'No losses'
            print('Largest Profit: $' + str(win_rate[4]) + ' Largest Loss: ' + minimum)
            print('Open trades: ' + str(status_sum[0]) + ' Closed trades: ' + str(status_sum[1]))
            print('Accounts: TOS: ' + str(acc_sum[0]) + ' IBG: ' + str(acc_sum[1]) + ' IBC: ' + str(acc_sum[2])) 
            print('Commissions: IBG: $' + str(comm_g) + ' IBC: $' + str(comm_c) + ' TOS: $' + str(comm_t))
            if o == False:
                print('Account Results: TOS $' + str(acc_results[0]) + ' IBG: $' + str(acc_results[1]) + ' IBC: $' + str(acc_results[2]))
                print('Number of times ES/MES traded: ' + str(utils.traded_most(symbols)))
                avg = self.calc_avg(query)
                print('Average trades per day: ' + str(avg))
                if len(loss_diff) > 0:
                    avg_loss = self.calc_avg_loss(loss_diff)
                    print('Average points lost per trade (ES/MES full futures only): -' + str(avg_loss) + ' points')
                    print('Number of times broke rules on ' + str(self.MAX_LOSS) + ' point ES/MES stop: ' + str(break_rule_stops))
        else:
            print('No trades found')

    def calc_avg_loss(self, diff):
        total = len(diff)
        points = 0
        avg = 0
        for d in diff:
            points += d
        
        if total > 0:
            avg = points / total

        return round(avg)

    def calc_avg(self, q):
        new_q = q.replace("SELECT *", "SELECT COUNT(*) AS total, COUNT(DISTINCT entry_date) AS total_days")
        rows = self.run_query(new_q)
        total = 0
        days = 0
        avg = 0
        for r in rows:
            total = r[0]
            days = r[1]

        if days > 0:
            avg = total / days
            
        return round(avg, 2)


    def view_trades_date(self):
        inc_day = False
        month = input('Enter a month (1-12)\n')
        year = input('Enter a year (2017-present)\n')
        m_o = input("View only selected month's range? (y/n)\n")
        month_options = ['y', 'n']

        c_m = utils.validate_int(month)
        c_y = utils.validate_int(year)

        if c_m != False:
            if not utils.month_check(c_m):
                print('Invalid month entered')
                return
        else:
            print('Invalid month integer entered')
            return

        if c_y != False:
            if not utils.year_check(c_y):
                print('Invalid year entered')
                return
        else:
            print('Invalid year integer entered')
            return

        if m_o.lower() in month_options:
            if m_o.lower() == 'n':
                day = input('Enter a day (1-31)\n')
                c_d = utils.validate_int(day)
                if c_d != False:
                    inc_day = True
                else:
                    print('Invald day integer entered')
                    return

        else:
            print('Month option must by y or n')
            return

        if inc_day:
            self.view_trades(c_m, c_y, c_d, False, m_o)
        else:
            self.view_trades(c_m, c_y, False, False, m_o)

    def view_open(self):
        self.view_trades(False, False, False, True)

    def view_exit_notes(self):
        utils.title('Early Exit Notes')
        #start with trades in most recent trading month
        begin = datetime.date.today().replace(day = 1)
        query = "SELECT symbol, notes FROM " + self.table_trades + " WHERE early_exit = 1 AND exit_date >= '" + str(begin) + "' ORDER BY exit_date"
        rows = self.run_query(query)
        if rows != False:
            for row in rows:
                print(row[0] + ' - ' + row[1])
                print('---------------------------------------------')
        else:
            print('No trades notes found')

    def trade_reasons(self):
        utils.title('Open Trade Reasons')
        #view all current open trades
        query = "SELECT symbol, entry, " + self.table_reasons + " FROM trades WHERE status = 'open' ORDER BY symbol"
        rows = self.run_query(query)
        if rows != False:
            for row in rows:
                print(row[0] + ' ' + str(utils.format_price(row[1])) + ' ' + row[2])
                print('---------------------------------------------')
        else:
            print('No open trades found')

    def loss_notes(self):
        utils.title('Loss Notes')
        opts = ['y', 'n']
        opt = input('View specific month for current year? (y or n):\n')
        if opt.lower() in opts:
            if opt.lower() == 'y':
                m_opt = input('Enter month (1-12):\n')
                m = utils.validate_int(m_opt)
                if m != False:
                    if utils.month_check(m):
                        print('Viewing ' + utils.get_month(m) + ' losses\n')
                        start = datetime.date.today().replace(day = 1, month = m)
                    else:
                        print('Month out of range\n')
                        return
                else:
                    print('Invalid month\n')
                    return
            else:
                start = datetime.date.today().replace(day = 1, month = 1)
        else:
            print('Invalid option\n')
            return

        query = "SELECT symbol, notes, result FROM " + self.table_trades + " WHERE result < 0 AND status = 'closed' AND exit_date >= '" + str(start) + "'"
        rows = self.run_query(query)
        if rows != False:
            total = 0
            for row in rows:
                total += row[2]
                print(row[0] + ' - $' + str(row[2]) + ' - ' + str(row[1]))
                print('---------------------------------------------')
            print('\nTotal losses: $' + str(total))
        else:
            print('No losing trades this month')

    def view_days(self):
        utils.title('Days - proft/loss')
        options = {
            1 : 'Last 5 days',
            2 : 'Last 10 days',
            3 : 'Last 20 days',
            4 : 'Last 30 days'
        }
        for k, v in options.items():
            print(str(k) + ' - ' + v)

        choice = input('\nChoose option\n')
        entered = utils.validate_int(choice)
        viewing = '\nViewing last '
        if entered != False:
            if entered == 1:
                sel = 5
                viewing += '5'
            elif entered == 2:
                sel = 10
                viewing += '10'
            elif entered == 3:
                sel = 20
                viewing += '20'
            elif entered == 4:
                sel = 30
                viewing += '30'
            else:
                print('Invalid option - exited')
                return
        else:
            print('Not a valid integer - exited')
            return

        viewing += ' days'
        start = datetime.date.today() - timedelta(days = sel)
        query = "SELECT SUM(result), exit_date FROM " + self.table_trades + " WHERE exit_date >= '" + str(start) + "' GROUP BY exit_date ORDER BY exit_date DESC"
        rows = self.run_query(query)
        if rows != False:
            total = 0
            print(viewing + '\n')
            for row in rows:
                total += row[0]
                print('DATE: ' + str(row[1]) + ' SUM: $' + str(row[0]))

            print('\nTotal: $' + str(total))
            print('\nNote: Excludes commissions')
        else:
            print('No results')

    def view_trade_by_id(self):
        utils.title('View trade by ID')
        enter = input('Enter ID\n')
        id = utils.validate_int(enter)
        if id != False:
            query = "SELECT * FROM " + self.table_trades + " WHERE id = " + str(id)
            try:
                cur = self.db.cursor()
                cur.execute(query)
                if cur.rowcount > 0:
                    row = cur.fetchone()
                    cols = [i[0] for i in cur.description]
                    c = 0
                    print('\nViewing ID: ' + str(id) + '\n')
                    for v in cols:
                        print(v + ' : ' + str(row[c]))
                        c += 1
                else:
                    print('No results found\n')
            except ValueError as e:
                print('Problem retrieving data\n')
        else:
            print('Not a valid integer\n')

    def get_locked_open(self):
        query = "SELECT result FROM " + self.table_trades + " WHERE status = 'open' AND result > 0"
        rows = self.run_query(query)
        if rows != False:
            total = 0
            for row in rows:
                total += row[0]
            return total
        else:
            return 0

    def view_open_ex_dates(self):
        utils.title('Open expiration dates')
        query = "SELECT id, symbol, exp_date FROM " + self.table_trades + " WHERE status = 'open' AND exp_date > '0000-00-00' ORDER BY exp_date"
        rows = self.run_query(query)
        if rows != False:
            for row in rows:
                print('{0:5} {1:13} {2:12}'.format('ID: ' + str(row[0]), 'SYMBOL: ' + row[1], 'EXPIRES: ' + str(row[2])))
        else:
            print('No results')
        
    def run_query(self, q, one = False):
        try:
            cur = self.db.cursor()
            cur.execute(q)
            if cur.rowcount > 0:
                if one == False:
                    return cur.fetchall()
                else:
                    return cur.fetchone()
            return False
        except ValueError as e:
            print('DB error: ' + e)
            return False

    def remove_trade(self):
        print('\nOption not availabe currently')

    def results_by_symbol(self):
        utils.title('Results by Symbol')
        symbol = input('Enter symbol: ')
        opt = ['y', 'n']
        show_range = False
        range = input('Show by month? (y or n)')
        if range.lower() in opt:
            if range.lower() == 'y':
                m = input('Enter month (1,2,etc)')
                m = utils.validate_int(m)
                if m != False:
                    if utils.month_check(m):
                        show_range = True
                        begin = datetime.date.today().replace(month = m, day = 1)
                        end = datetime.date.today().replace(month = m + 1, day = 1) - datetime.timedelta(days = 1)
                    else:
                        print(str(m) + ' month out of range')
                        return
                else:
                    print(m + ' not a valid month integer')
        else:
            print(range + ' Invalid option')
            return

        symbol = symbol.upper()
        q = "SELECT result, exit_date FROM " + self.table_trades + " WHERE symbol = '" + symbol + "' AND status = 'closed'"
        if show_range:
            print('\nViewing ' + utils.get_month(m) + ' results')
            q += " AND exit_date >= '" + str(begin) + "' AND exit_date <= '" + str(end) + "'"
        q += " ORDER BY exit_date DESC"
    
        r = self.run_query(q)
        if r != False:
            t = 0
            t_p = 0
            t_l = 0
            ps = ''
            ls = ''
            pc = 0
            lc = 0
            for row in r:
                if row[0] > 0:
                    t_p += row[0]
                    ps += str(row[1]) + ' - $' + str(row[0]) + '\n'
                    pc += 1
                else:
                    t_l += row[0]
                    ls += str(row[1]) + ' - $' + str(row[0]) + '\n'
                    lc += 1

            t = t_p + t_l
            print('\nWon \n')
            print(ps)
            print('Total: ' + str(pc))
            print('\nLossed\n')
            print(ls)
            print('Total: ' + str(lc))
            print('\nGross proft: $' + str(t_p))
            print('Gross loss: $' + str(t_l))
            print('Net result for symbol ' + symbol + ': $' + str(t))
        else:
            print('\nNo results for symbol: ' + symbol)

    def ib_minimums(self):
        t = datetime.date.today().replace(day = 1)
        c = utils.get_month(t.month)
        q = "SELECT entry_comm, exit_comm, entry_date, exit_date, account FROM " + self.table_trades + " WHERE (entry_date >= '" + str(t) + "' OR exit_date >= '" + str(t) + "')"
        r = self.run_query(q)
        if r != False:
            g_en = 0
            g_ex = 0
            b_en = 0
            b_ex = 0
            t_en = 0
            t_ex = 0
            max = 10
            for row in r:
                if row[4] == 'ibg':
                    if row[2] != None:
                        if str(row[2]) >= str(t):
                            g_en += row[0]
                    if row[3] != None:
                        if str(row[3]) >= str(t):
                            g_ex += row[1]
                elif row[4] == 'ibc':
                    if row[2] != None:
                        if str(row[2]) >= str(t):
                            b_en += row[0]
                    if row[3] != None:
                        if str(row[3]) >= str(t):
                            b_ex += row[1]
                else:
                    if row[2] != None:
                        if str(row[2]) >= str(t):
                            t_en += row[0]
                    if row[3] != None:
                        if str(row[3]) >= str(t):
                            t_ex += row[1]

            t_g = g_en + g_ex
            t_b = b_en + b_ex
            t_t = t_en + t_ex
            if t_g < max:
                print('IBG minimum not met yet for ' + c + ', so far about: $' + str(t_g))
            else:
                print('IBG ' + c + ' commissions: $' + str(t_g))
            if t_b < max:
                print('IBC minimum not met yet for ' + c + ', so far about: $' + str(t_b))
            else:
                print('IBC ' + c + ' commissions: $' + str(t_b))
            if t_t < max:
                print('TOS minimum not met yet for ' + c + ', so far about: $' + str(t_t))
            else:
                print('TOS ' + c + ' commissions: $' + str(t_t))

            print('Total spent: $' + str(t_g + t_b + t_t))

    def show_weekly_plan(self):
    	utils.title('Weekly Trading Plan')
    	q = "SELECT plan, plan_date FROM " + self.table_plan + " ORDER BY id DESC LIMIT 1"
    	r = self.run_query(q, True)
    	print('Plan for the week beginning on: ' + str(r[1]))
    	print('---------------------------------------')
    	print(r[0])

    def view_by_account(self):
    	utils.title('Trades By Account')
    	account = input('Enter an account\n')
    	if account.lower() not in self.accounts:
    		print('Not a valid account\n')
    		return
    	opt = ['open', 'closed']
    	o = False
    	t = input('Open or Closed trades\n')
    	if t.lower() not in opt:
    		print('Not a valid type\n')
    		return
    	
    	if t.lower() == 'open':
    		o = True

    	self.view_trades(False, False, False, o, False, account.lower())

        

# class end - start running

t = TradeLog()
t.menu()

print('\n--------\n')
t.check_last_rules_viewed()
t.check_expirations()
t.check_exit_date_open()
t.ib_minimums()

options = {
    1 : t.view_trades,
    2 : t.trade_entry,
    3 : t.remove_trade,
    4 : t.view_open,
    5 : t.menu,
    6 : t.show_rules,
    7 : utils.exit_app,
    8 : t.show_watchlist,
    9 : t.show_trade_plan,
    10 : t.add_idea,
    11 : t.view_trades_date,
    12 : t.view_exit_notes,
    13 : t.trade_reasons,
    14 : t.loss_notes,
    15 : t.view_days,
    16 : t.view_trade_by_id,
    17 : t.view_open_ex_dates,
    18 : t.results_by_symbol,
    19 : t.show_lessons,
    20 : t.show_weekly_plan,
    21 : t.view_by_account
}

while True:
    option = input('\nChoose option (5 => menu)\n')
    entered = utils.validate_int(option)

    if(entered != False):
        if entered in options:
            options[entered]()
        else:
            print('Not a valid option')

        print('\nYou entered ', entered)
    else:
        print('Not a vaild option')

t.db.close()
