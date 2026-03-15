"""
Loan Amortization Calculator
Calculates payment schedules, extra payment scenarios, and payoff analysis
"""

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import csv
from assets.Logger import Logger
logger = Logger()

class LoanCalculator:
    """Calculate loan amortization schedules and what-if scenarios"""
    
    def __init__(self, principal, annual_rate, monthly_payment, start_date=None):
        """
        Initialize loan calculator.
        
        Args:
            principal: Initial loan amount
            annual_rate: Annual interest rate (as decimal, e.g., 0.05 for 5%)
            monthly_payment: Monthly payment amount
            start_date: Loan start date (defaults to today)
        """
        self.principal = float(principal)
        self.annual_rate = float(annual_rate)
        self.monthly_rate = self.annual_rate / 12.0
        self.monthly_payment = float(monthly_payment)
        self.start_date = start_date or date.today()
        logger.debug("LoanCalculator", f"Initialized with principal=${self.principal:.2f}, annual_rate={self.annual_rate:.4f}, monthly_payment=${self.monthly_payment:.2f}, start_date={self.start_date}")
    
    def calculate_amortization_schedule(self, extra_monthly=0.0, lump_sum=0.0, lump_sum_month=0):
        """
        Calculate full amortization schedule.
        
        Args:
            extra_monthly: Extra amount to pay each month
            lump_sum: One-time lump sum payment
            lump_sum_month: Month number to apply lump sum (0 = no lump sum)
        
        Returns:
            list: Schedule with payment details for each month
        """
        try:
            logger.debug("LoanCalculator", f"Calculating amortization schedule with extra_monthly=${extra_monthly:.2f}, lump_sum=${lump_sum:.2f}, lump_sum_month={lump_sum_month}")
            balance = self.principal
            total_payment = self.monthly_payment + extra_monthly
            schedule = []
            payment_num = 0
            current_date = self.start_date
            
            while balance > 0.01:  # Continue until balance is essentially zero
                payment_num += 1
                
                # Calculate interest for this period
                interest_payment = balance * self.monthly_rate
                
                # Calculate principal payment
                principal_payment = min(total_payment - interest_payment, balance)
                
                # Apply lump sum if this is the specified month
                if lump_sum_month > 0 and payment_num == lump_sum_month:
                    principal_payment += lump_sum
                    actual_payment = total_payment + lump_sum
                else:
                    actual_payment = min(total_payment, balance + interest_payment)
                
                # Update balance
                balance -= principal_payment
                balance = max(0, balance)  # Prevent negative balance
                
                # Add to schedule
                schedule.append({
                    'payment_number': payment_num,
                    'date': current_date.isoformat(),
                    'payment': actual_payment,
                    'principal': principal_payment,
                    'interest': interest_payment,
                    'extra_principal': extra_monthly + (lump_sum if payment_num == lump_sum_month else 0),
                    'balance': balance
                })
                
                # Move to next month
                current_date = current_date + relativedelta(months=1)
                
                # Safety check to prevent infinite loop
                if payment_num > 1000:
                    logger.warning("LoanCalculator", f"Payment count exceeded 1000, breaking loop")
                    break
            
            total_interest = sum(p['interest'] for p in schedule)
            logger.info("LoanCalculator", f"Generated amortization schedule with {len(schedule)} payments, total_interest=${total_interest:.2f}")
            return schedule
        except Exception as e:
            logger.error("LoanCalculator", f"Error calculating amortization schedule: {str(e)}")
            raise
    
    def calculate_standard_schedule(self):
        """Calculate standard amortization schedule with no extra payments"""
        logger.debug("LoanCalculator", "Calculating standard schedule with no extra payments")
        return self.calculate_amortization_schedule()
    
    def calculate_with_extra_monthly(self, extra_amount):
        """Calculate schedule with extra monthly payments"""
        logger.debug("LoanCalculator", f"Calculating schedule with extra monthly payment=${extra_amount:.2f}")
        return self.calculate_amortization_schedule(extra_monthly=extra_amount)
    
    def calculate_with_lump_sum(self, lump_sum, month_number):
        """Calculate schedule with a one-time lump sum payment"""
        logger.debug("LoanCalculator", f"Calculating schedule with lump sum=${lump_sum:.2f} at month {month_number}")
        return self.calculate_amortization_schedule(lump_sum=lump_sum, lump_sum_month=month_number)
    
    def get_summary_stats(self, schedule):
        """
        Calculate summary statistics for a payment schedule.
        
        Args:
            schedule: Amortization schedule from calculate_amortization_schedule()
        
        Returns:
            dict: Summary statistics
        """
        if not schedule:
            logger.debug("LoanCalculator", "get_summary_stats called with empty schedule")
            return {
                'total_payments': 0,
                'total_paid': 0.0,
                'total_interest': 0.0,
                'total_principal': 0.0,
                'payoff_date': None,
                'months_to_payoff': 0
            }
        
        total_paid = sum(p['payment'] for p in schedule)
        total_interest = sum(p['interest'] for p in schedule)
        total_principal = sum(p['principal'] for p in schedule)
        
        stats = {
            'total_payments': len(schedule),
            'total_paid': total_paid,
            'total_interest': total_interest,
            'total_principal': total_principal,
            'payoff_date': schedule[-1]['date'],
            'months_to_payoff': len(schedule)
        }
        logger.debug("LoanCalculator", f"Generated summary stats: {len(schedule)} payments, total_paid=${total_paid:.2f}, total_interest=${total_interest:.2f}")
        return stats
    
    def compare_scenarios(self, extra_monthly=0.0, lump_sum=0.0, lump_sum_month=0):
        """
        Compare standard payment vs accelerated payment scenarios.
        
        Args:
            extra_monthly: Extra monthly payment
            lump_sum: Lump sum payment
            lump_sum_month: Month to apply lump sum
        
        Returns:
            dict: Comparison of standard vs accelerated scenarios
        """
        try:
            logger.debug("LoanCalculator", f"Comparing scenarios: extra_monthly=${extra_monthly:.2f}, lump_sum=${lump_sum:.2f}")
            standard = self.calculate_standard_schedule()
            accelerated = self.calculate_amortization_schedule(extra_monthly, lump_sum, lump_sum_month)
            
            standard_stats = self.get_summary_stats(standard)
            accelerated_stats = self.get_summary_stats(accelerated)
            
            # Calculate savings
            interest_saved = standard_stats['total_interest'] - accelerated_stats['total_interest']
            months_saved = standard_stats['months_to_payoff'] - accelerated_stats['months_to_payoff']
            
            logger.info("LoanCalculator", f"Scenario comparison: interest_saved=${interest_saved:.2f}, months_saved={months_saved}, years_saved={months_saved/12.0:.2f}")
            return {
                'standard': standard_stats,
                'accelerated': accelerated_stats,
                'interest_saved': interest_saved,
                'months_saved': months_saved,
                'years_saved': months_saved / 12.0
            }
        except Exception as e:
            logger.error("LoanCalculator", f"Error comparing scenarios: {str(e)}")
            raise
    
    def calculate_remaining_balance(self, months_paid):
        """
        Calculate remaining balance after a certain number of payments.
        
        Args:
            months_paid: Number of payments already made
        
        Returns:
            float: Remaining balance
        """
        try:
            logger.debug("LoanCalculator", f"Calculating remaining balance after {months_paid} months paid")
            schedule = self.calculate_standard_schedule()
            
            if months_paid >= len(schedule):
                logger.debug("LoanCalculator", f"months_paid ({months_paid}) exceeds schedule length ({len(schedule)}), returning 0.0")
                return 0.0
            
            if months_paid < 0:
                logger.debug("LoanCalculator", f"months_paid is negative ({months_paid}), returning principal")
                return self.principal
            
            balance = schedule[months_paid]['balance']
            logger.debug("LoanCalculator", f"Remaining balance after {months_paid} months: ${balance:.2f}")
            return balance
        except Exception as e:
            logger.error("LoanCalculator", f"Error calculating remaining balance: {str(e)}")
            raise
    
    def calculate_monthly_payment_needed(self, target_months):
        """
        Calculate monthly payment needed to pay off loan in target months.
        
        Args:
            target_months: Desired payoff timeframe in months
        
        Returns:
            float: Required monthly payment
        """
        try:
            logger.debug("LoanCalculator", f"Calculating monthly payment needed to pay off in {target_months} months")
            if target_months <= 0 or self.monthly_rate == 0:
                logger.debug("LoanCalculator", f"Invalid parameters: target_months={target_months}, monthly_rate={self.monthly_rate}, returning 0.0")
                return 0.0
            
            # Monthly payment formula: P * [r(1+r)^n] / [(1+r)^n - 1]
            # Where P = principal, r = monthly rate, n = number of payments
            r = self.monthly_rate
            n = target_months
            
            payment = self.principal * (r * (1 + r)**n) / ((1 + r)**n - 1)
            logger.debug("LoanCalculator", f"Calculated required monthly payment: ${payment:.2f} for {target_months} months")
            return payment
        except Exception as e:
            logger.error("LoanCalculator", f"Error calculating monthly payment needed: {str(e)}")
            raise
    
    def calculate_payoff_date(self, extra_monthly=0.0):
        """
        Calculate payoff date with optional extra payments.
        
        Args:
            extra_monthly: Extra monthly payment
        
        Returns:
            dict: Payoff information
        """
        try:
            logger.debug("LoanCalculator", f"Calculating payoff date with extra_monthly=${extra_monthly:.2f}")
            schedule = self.calculate_amortization_schedule(extra_monthly=extra_monthly)
            stats = self.get_summary_stats(schedule)
            
            payoff_date = datetime.strptime(stats['payoff_date'], '%Y-%m-%d').date()
            months_remaining = stats['months_to_payoff']
            years_remaining = months_remaining / 12.0
            
            logger.info("LoanCalculator", f"Payoff date calculated: {payoff_date}, {months_remaining} months remaining, total_interest=${stats['total_interest']:.2f}")
            return {
                'payoff_date': payoff_date,
                'months_remaining': months_remaining,
                'years_remaining': years_remaining,
                'total_interest': stats['total_interest']
            }
        except Exception as e:
            logger.error("LoanCalculator", f"Error calculating payoff date: {str(e)}")
            raise
    
    def export_schedule_to_csv(self, schedule, filename):
        """
        Export amortization schedule to CSV file.
        
        Args:
            schedule: Amortization schedule
            filename: Output filename
        
        Returns:
            bool: Success status
        """
        try:
            logger.debug("LoanCalculator", f"Exporting schedule with {len(schedule)} payments to {filename}")
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'Payment #',
                    'Date',
                    'Payment',
                    'Principal',
                    'Interest',
                    'Extra Principal',
                    'Remaining Balance'
                ])
                
                # Data rows
                for payment in schedule:
                    writer.writerow([
                        payment['payment_number'],
                        payment['date'],
                        f"${payment['payment']:.2f}",
                        f"${payment['principal']:.2f}",
                        f"${payment['interest']:.2f}",
                        f"${payment['extra_principal']:.2f}",
                        f"${payment['balance']:.2f}"
                    ])
                
                # Summary at the end
                stats = self.get_summary_stats(schedule)
                writer.writerow([])
                writer.writerow(['SUMMARY'])
                writer.writerow(['Total Payments', stats['total_payments']])
                writer.writerow(['Total Amount Paid', f"${stats['total_paid']:.2f}"])
                writer.writerow(['Total Interest Paid', f"${stats['total_interest']:.2f}"])
                writer.writerow(['Total Principal Paid', f"${stats['total_principal']:.2f}"])
                writer.writerow(['Payoff Date', stats['payoff_date']])
            
            logger.info("LoanCalculator", f"Successfully exported schedule to {filename}")
            return True
        except Exception as e:
            logger.error("LoanCalculator", f"Failed to export schedule to {filename}: {str(e)}")
            return False
    
    def get_payment_breakdown_by_year(self, schedule):
        """
        Group payments by year for annual summary.
        
        Args:
            schedule: Amortization schedule
        
        Returns:
            dict: Annual payment breakdown
        """
        try:
            logger.debug("LoanCalculator", f"Generating yearly payment breakdown for {len(schedule)} payments")
            yearly_data = {}
            
            for payment in schedule:
                payment_date = datetime.strptime(payment['date'], '%Y-%m-%d').date()
                year = payment_date.year
                
                if year not in yearly_data:
                    yearly_data[year] = {
                        'payments': 0,
                        'total_paid': 0.0,
                        'total_principal': 0.0,
                        'total_interest': 0.0,
                        'ending_balance': 0.0
                    }
                
                yearly_data[year]['payments'] += 1
                yearly_data[year]['total_paid'] += payment['payment']
                yearly_data[year]['total_principal'] += payment['principal']
                yearly_data[year]['total_interest'] += payment['interest']
                yearly_data[year]['ending_balance'] = payment['balance']
            
            logger.debug("LoanCalculator", f"Generated yearly breakdown for {len(yearly_data)} years")
            return yearly_data
        except Exception as e:
            logger.error("LoanCalculator", f"Error generating yearly breakdown: {str(e)}")
            raise
    
    def calculate_interest_rate_from_payment(self, principal, monthly_payment, months):
        """
        Calculate interest rate given principal, payment, and term.
        Uses Newton's method for approximation.
        
        Args:
            principal: Loan amount
            monthly_payment: Monthly payment
            months: Loan term in months
        
        Returns:
            float: Annual interest rate (as decimal)
        """
        try:
            logger.debug("LoanCalculator", f"Calculating interest rate: principal=${principal:.2f}, monthly_payment=${monthly_payment:.2f}, months={months}")
            # Initial guess: 5% annual rate
            rate = 0.05 / 12
            
            # Newton's method iteration
            for iteration in range(100):
                # Calculate payment with current rate guess
                if rate == 0:
                    calc_payment = principal / months
                else:
                    calc_payment = principal * (rate * (1 + rate)**months) / ((1 + rate)**months - 1)
                
                # If close enough, return
                if abs(calc_payment - monthly_payment) < 0.01:
                    annual_rate = rate * 12
                    logger.debug("LoanCalculator", f"Converged on interest rate={annual_rate:.4f} after {iteration} iterations")
                    return annual_rate  # Convert to annual rate
                
                # Adjust rate
                if calc_payment > monthly_payment:
                    rate *= 0.95  # Reduce rate
                else:
                    rate *= 1.05  # Increase rate
            
            annual_rate = rate * 12
            logger.warning("LoanCalculator", f"Interest rate calculation did not converge after 100 iterations, returning {annual_rate:.4f}")
            return annual_rate  # Return annual rate
        except Exception as e:
            logger.error("LoanCalculator", f"Error calculating interest rate: {str(e)}")
            raise
    
    @staticmethod
    def calculate_loan_payment(principal, annual_rate, months):
        """
        Calculate monthly payment for a loan.
        
        Args:
            principal: Loan amount
            annual_rate: Annual interest rate (decimal)
            months: Loan term in months
        
        Returns:
            float: Monthly payment amount
        """
        try:
            logger.debug("LoanCalculator", f"Static method: calculating loan payment for principal=${principal:.2f}, annual_rate={annual_rate:.4f}, months={months}")
            if annual_rate == 0:
                payment = principal / months
                logger.debug("LoanCalculator", f"Zero interest rate, simple division payment=${payment:.2f}")
                return payment
            
            monthly_rate = annual_rate / 12
            payment = principal * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
            logger.debug("LoanCalculator", f"Calculated monthly payment=${payment:.2f}")
            return payment
        except Exception as e:
            logger.error("LoanCalculator", f"Error calculating loan payment: {str(e)}")
            raise
