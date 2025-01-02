from flask import Blueprint, render_template, session, redirect, url_for, flash, request
import mysql.connector

bidding_routes = Blueprint('bidding_routes', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host="db",
        user="user",
        password="password",
        database="mydatabase"
    )

@bidding_routes.route('/wallet', methods=['GET'])
def view_wallet():
    if 'user_id' not in session:
        flash('You must be logged in to view your wallet.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch wallet balance
        wallet_query = """
            SELECT funds
            FROM Wallet
            WHERE user_id = %s;
        """
        cursor.execute(wallet_query, (user_id,))
        wallet = cursor.fetchone()

        # If the wallet does not exist, create it
        if not wallet:
            cursor.execute("INSERT INTO Wallet (user_id, funds) VALUES (%s, 0.00);", (user_id,))
            db.commit()
            wallet = {'funds': 0.00}

        return render_template('wallet.html', funds=wallet['funds'])

    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('auth_routes.dashboard'))

    finally:
        cursor.close()
        db.close()

@bidding_routes.route('/wallet/add_funds', methods=['POST'])
def add_funds():
    if 'user_id' not in session:
        flash('You must be logged in to add funds.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']
    amount = request.form.get('amount', '').strip()

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive.")

    except ValueError:
        flash('Invalid amount. Please enter a valid positive number.', 'danger')
        return redirect(url_for('bidding_routes.view_wallet'))

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Update wallet balance
        update_wallet_query = """
            UPDATE Wallet
            SET funds = funds + %s
            WHERE user_id = %s;
        """
        cursor.execute(update_wallet_query, (amount, user_id))
        db.commit()

        flash(f'Successfully added ${amount:.2f} to your wallet.', 'success')
        return redirect(url_for('bidding_routes.view_wallet'))

    except mysql.connector.Error as err:
        db.rollback()
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('bidding_routes.view_wallet'))

    finally:
        cursor.close()
        db.close()


@bidding_routes.route('/make_bid/<int:ad_id>', methods=['POST'])
def make_bid(ad_id):
    if 'user_id' not in session:
        flash('You must be logged in to make a bid.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']
    bid_amount = request.form.get('bid_amount', '').strip()

    try:
        bid_amount = float(bid_amount)
        if bid_amount <= 0:
            raise ValueError("Invalid bid amount")
    except ValueError:
        flash('Please enter a valid positive bid amount.', 'danger')
        return redirect(url_for('listing_routes.view_ad_details', ad_id=ad_id))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Check if the ad exists and if the user owns it
        ad_query = """
            SELECT seller_id FROM VehicleAd WHERE ad_id = %s;
        """
        cursor.execute(ad_query, (ad_id,))
        ad = cursor.fetchone()

        if not ad:
            flash('The ad does not exist.', 'danger')
            return redirect(url_for('listing_routes.view_listings'))

        if ad['seller_id'] == user_id:
            flash('You cannot bid on your own ads.', 'danger')
            return redirect(url_for('listing_routes.view_ad_details', ad_id=ad_id))

        # Check if the user already has a pending bid on this ad
        bid_query = """
            SELECT bid_id FROM Bid 
            WHERE ad_id = %s AND buyer_id = %s AND status = 'waiting';
        """
        cursor.execute(bid_query, (ad_id, user_id))
        existing_bid = cursor.fetchone()

        if existing_bid:
            flash('You should wait for your previous bids to be resolved.', 'warning')
            return redirect(url_for('listing_routes.view_ad_details', ad_id=ad_id))

        # Insert the new bid
        insert_bid_query = """
            INSERT INTO Bid (amount, status, buyer_id, ad_id)
            VALUES (%s, 'waiting', %s, %s);
        """
        cursor.execute(insert_bid_query, (bid_amount, user_id, ad_id))
        db.commit()

        flash('Your bid has been placed successfully.', 'success')
        return redirect(url_for('bidding_routes.view_my_bids'))

    except mysql.connector.Error as err:
        db.rollback()
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('listing_routes.view_ad_details', ad_id=ad_id))

    finally:
        cursor.close()
        db.close()

@bidding_routes.route('/my_bids', methods=['GET'])
def view_my_bids():
    if 'user_id' not in session:
        flash('You must be logged in to view your bids.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch bids made by the user
        user_bids_query = """
            SELECT Bid.amount, Bid.status, Bid.counter_bid, Bid.created_at, 
                   VehicleAd.ad_id, VehicleAd.title, VehicleAd.status AS ad_status, Photo.content AS photo_url,
                   User.username AS seller_username, Bid.bid_id,
                   EXISTS (
                       SELECT 1 
                       FROM Bid b2 
                       WHERE b2.ad_id = Bid.ad_id 
                         AND b2.buyer_id = Bid.buyer_id 
                         AND b2.status = 'waiting'
                   ) AS has_waiting_bid,
                   EXISTS (
                        SELECT 1 
                        FROM Bid b2 
                        WHERE b2.ad_id = Bid.ad_id 
                            AND b2.buyer_id = Bid.buyer_id 
                            AND b2.status = 'approved'
                    ) AS has_approved_bid
            FROM Bid
            JOIN VehicleAd ON Bid.ad_id = VehicleAd.ad_id
            LEFT JOIN Photo ON VehicleAd.vehicle_id = Photo.vehicle_id AND Photo.is_primary = TRUE
            JOIN User ON VehicleAd.seller_id = User.user_id
            WHERE Bid.buyer_id = %s;
        """
        cursor.execute(user_bids_query, (user_id,))
        user_bids = cursor.fetchall()

        # Fetch bids made on the user's ads
        user_ads_bids_query = """
            SELECT Bid.amount, Bid.status, Bid.created_at, 
                   VehicleAd.ad_id, VehicleAd.title, Photo.content AS photo_url,
                   Bid.bid_id, User.username AS bidder_username
            FROM Bid
            JOIN VehicleAd ON Bid.ad_id = VehicleAd.ad_id
            LEFT JOIN Photo ON VehicleAd.vehicle_id = Photo.vehicle_id AND Photo.is_primary = TRUE
            JOIN User ON Bid.buyer_id = User.user_id
            WHERE VehicleAd.seller_id = %s;
        """
        cursor.execute(user_ads_bids_query, (user_id,))
        user_ads_bids = cursor.fetchall()

        return render_template('my_bids.html', user_bids=user_bids, user_ads_bids=user_ads_bids)

    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('auth_routes.dashboard'))

    finally:
        cursor.close()
        db.close()


@bidding_routes.route('/reject_bid/<int:bid_id>', methods=['POST'])
def reject_bid(bid_id):
    if 'user_id' not in session:
        flash('You must be logged in to reject a bid.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Validate that the bid exists and belongs to an ad owned by the user
        bid_query = """
            SELECT Bid.ad_id, VehicleAd.seller_id
            FROM Bid
            JOIN VehicleAd ON Bid.ad_id = VehicleAd.ad_id
            WHERE Bid.bid_id = %s AND Bid.status = 'waiting';
        """
        cursor.execute(bid_query, (bid_id,))
        bid = cursor.fetchone()

        if not bid:
            flash('The bid does not exist or is not eligible for rejection.', 'danger')
            return redirect(url_for('bidding_routes.view_my_bids'))

        if bid['seller_id'] != user_id:
            flash('You are not authorized to reject this bid.', 'danger')
            return redirect(url_for('bidding_routes.view_my_bids'))

        # Update the bid status to rejected
        update_query = """
            UPDATE Bid
            SET status = 'rejected'
            WHERE bid_id = %s;
        """
        cursor.execute(update_query, (bid_id,))
        db.commit()

        flash('The bid has been successfully rejected.', 'success')
        return redirect(url_for('bidding_routes.view_my_bids'))

    except mysql.connector.Error as err:
        db.rollback()
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('bidding_routes.view_my_bids'))

    finally:
        cursor.close()
        db.close()

@bidding_routes.route('/make_another_bid/<int:ad_id>', methods=['POST'])
def make_another_bid(ad_id):
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash('You must be logged in to make another bid.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']
    new_bid_amount = request.form.get('bid_amount', '').strip()

    # Validate the new bid amount
    try:
        new_bid_amount = float(new_bid_amount)
        if new_bid_amount <= 0:
            raise ValueError("Invalid bid amount.")
    except ValueError:
        flash('Please enter a valid positive bid amount.', 'danger')
        return redirect(url_for('bidding_routes.view_my_bids'))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Validate if the user has a rejected bid for this ad
        rejected_bid_query = """
            SELECT bid_id FROM Bid
            WHERE ad_id = %s AND buyer_id = %s AND status = 'rejected';
        """
        cursor.execute(rejected_bid_query, (ad_id, user_id))
        rejected_bid = cursor.fetchone()

        if not rejected_bid:
            flash('You cannot create another bid for this ad.', 'danger')
            return redirect(url_for('bidding_routes.view_my_bids'))

        # Check if the user already has a pending bid for this ad
        pending_bid_query = """
            SELECT bid_id FROM Bid
            WHERE ad_id = %s AND buyer_id = %s AND status = 'waiting';
        """
        cursor.execute(pending_bid_query, (ad_id, user_id))
        pending_bid = cursor.fetchone()

        if pending_bid:
            flash('You already have a pending bid for this ad. Please wait for it to be resolved.', 'warning')
            return redirect(url_for('bidding_routes.view_my_bids'))

        # Insert the new bid into the Bid table
        insert_bid_query = """
            INSERT INTO Bid (amount, status, buyer_id, ad_id)
            VALUES (%s, 'waiting', %s, %s);
        """
        cursor.execute(insert_bid_query, (new_bid_amount, user_id, ad_id))
        db.commit()

        flash('Your new bid has been placed successfully.', 'success')
        return redirect(url_for('bidding_routes.view_my_bids'))

    except mysql.connector.Error as err:
        db.rollback()
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('bidding_routes.view_my_bids'))

    finally:
        cursor.close()
        db.close()

@bidding_routes.route('/counter_offer/<int:bid_id>', methods=['POST'])
def counter_offer(bid_id):
    if 'user_id' not in session:
        flash('You must be logged in to make a counter offer.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']
    counter_offer_value = request.form.get('counter_offer', '').strip()

    try:
        # Validate the counter-offer value
        counter_offer_value = float(counter_offer_value)
        if counter_offer_value <= 0:
            raise ValueError("Invalid counter-offer amount.")

    except ValueError:
        flash('Please enter a valid positive counter-offer amount.', 'danger')
        return redirect(url_for('bidding_routes.view_my_bids'))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Validate bid and ad ownership
        bid_query = """
            SELECT Bid.bid_id, VehicleAd.seller_id
            FROM Bid
            JOIN VehicleAd ON Bid.ad_id = VehicleAd.ad_id
            WHERE Bid.bid_id = %s AND Bid.status = 'waiting';
        """
        cursor.execute(bid_query, (bid_id,))
        bid = cursor.fetchone()

        if not bid:
            flash('The bid does not exist or is not eligible for a counter offer.', 'danger')
            return redirect(url_for('bidding_routes.view_my_bids'))

        if bid['seller_id'] != user_id:
            flash('You are not authorized to make a counter offer on this bid.', 'danger')
            return redirect(url_for('bidding_routes.view_my_bids'))

        # Update the bid with the counter-offer value (leave status as 'waiting')
        update_query = """
            UPDATE Bid
            SET counter_bid = %s
            WHERE bid_id = %s;
        """
        cursor.execute(update_query, (counter_offer_value, bid_id))
        db.commit()

        flash('Counter offer has been successfully submitted.', 'success')
        return redirect(url_for('bidding_routes.view_my_bids'))

    except mysql.connector.Error as err:
        db.rollback()
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('bidding_routes.view_my_bids'))

    finally:
        cursor.close()
        db.close()
        
@bidding_routes.route('/approve_bid/<int:bid_id>', methods=['POST'])
def approve_bid(bid_id):
    if 'user_id' not in session:
        flash('You must be logged in to approve a bid.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Validate bid and ownership
        bid_query = """
            SELECT Bid.ad_id, VehicleAd.seller_id
            FROM Bid
            JOIN VehicleAd ON Bid.ad_id = VehicleAd.ad_id
            WHERE Bid.bid_id = %s AND Bid.status = 'waiting';
        """
        cursor.execute(bid_query, (bid_id,))
        bid = cursor.fetchone()

        if not bid:
            flash('The bid does not exist or is not eligible for approval.', 'danger')
            return redirect(url_for('bidding_routes.view_my_bids'))

        if bid['seller_id'] != user_id:
            flash('You are not authorized to approve this bid.', 'danger')
            return redirect(url_for('bidding_routes.view_my_bids'))

        # Approve the selected bid
        approve_query = """
            UPDATE Bid
            SET status = 'approved'
            WHERE bid_id = %s;
        """
        cursor.execute(approve_query, (bid_id,))

        # Reject all other bids for the same ad
        reject_other_bids_query = """
            UPDATE Bid
            SET status = 'rejected'
            WHERE ad_id = %s AND bid_id != %s AND status = 'waiting';
        """
        cursor.execute(reject_other_bids_query, (bid['ad_id'], bid_id))
        db.commit()

        flash('The bid has been successfully approved.', 'success')
        return redirect(url_for('bidding_routes.view_my_bids'))

    except mysql.connector.Error as err:
        db.rollback()
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('bidding_routes.view_my_bids'))

    finally:
        cursor.close()
        db.close()


@bidding_routes.route('/confirm_transaction/<int:bid_id>', methods=['GET'])
def confirm_transaction(bid_id):
    if 'user_id' not in session:
        flash('You must be logged in to proceed with a transaction.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch approved bid details
        bid_query = """
            SELECT Bid.amount, Bid.ad_id, VehicleAd.title, VehicleAd.vehicle_id, 
                   Photo.content AS photo_url, User.username AS seller_username, 
                   Wallet.funds AS buyer_funds, Bid.bid_id
            FROM Bid
            JOIN VehicleAd ON Bid.ad_id = VehicleAd.ad_id
            JOIN User ON VehicleAd.seller_id = User.user_id
            LEFT JOIN Photo ON VehicleAd.vehicle_id = Photo.vehicle_id AND Photo.is_primary = TRUE
            LEFT JOIN Wallet ON Wallet.user_id = %s
            WHERE Bid.bid_id = %s AND Bid.status = 'approved';
        """
        cursor.execute(bid_query, (user_id, bid_id))
        bid_details = cursor.fetchone()

        if not bid_details:
            flash('Invalid or unavailable transaction.', 'danger')
            return redirect(url_for('bidding_routes.view_my_bids'))

        return render_template('confirm_transaction.html', bid=bid_details)

    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('bidding_routes.view_my_bids'))

    finally:
        cursor.close()
        db.close()

@bidding_routes.route('/commit_transaction/<int:bid_id>', methods=['POST'])
def commit_transaction(bid_id):
    if 'user_id' not in session:
        flash('You must be logged in to proceed with a transaction.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch bid and wallet details
        bid_query = """
            SELECT Bid.amount, Bid.ad_id, VehicleAd.seller_id, Wallet.funds AS buyer_funds
            FROM Bid
            JOIN VehicleAd ON Bid.ad_id = VehicleAd.ad_id
            LEFT JOIN Wallet ON Wallet.user_id = %s
            WHERE Bid.bid_id = %s AND Bid.status = 'approved';
        """
        cursor.execute(bid_query, (user_id, bid_id))
        bid_details = cursor.fetchone()

        if not bid_details:
            flash('Invalid or unavailable transaction.', 'danger')
            return redirect(url_for('bidding_routes.view_my_bids'))

        if bid_details['buyer_funds'] < bid_details['amount']:
            flash('Insufficient funds in your wallet to complete this transaction.', 'danger')
            return redirect(url_for('bidding_routes.confirm_transaction', bid_id=bid_id))

        # Deduct funds and update the ad status
        update_wallet_query = """
            UPDATE Wallet SET funds = funds - %s WHERE user_id = %s;
        """
        update_ad_query = """
            UPDATE VehicleAd SET status = 'sold' WHERE ad_id = %s;
        """
        insert_transaction_query = """
            INSERT INTO Transaction (amount, buyer_id, seller_id, ad_id)
            VALUES (%s, %s, %s, %s);
        """

        cursor.execute(update_wallet_query, (bid_details['amount'], user_id))
        cursor.execute(update_ad_query, (bid_details['ad_id'],))
        cursor.execute(insert_transaction_query, (bid_details['amount'], user_id, bid_details['seller_id'], bid_details['ad_id']))
        db.commit()

        flash('Transaction successfully completed!', 'success')
        return redirect(url_for('bidding_routes.view_transactions'))

    except mysql.connector.Error as err:
        db.rollback()
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('bidding_routes.view_my_bids'))

    finally:
        cursor.close()
        db.close()

@bidding_routes.route('/transactions', methods=['GET'])
def view_transactions():
    if 'user_id' not in session:
        flash('You must be logged in to view your transactions.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch transactions as buyer
        bought_query = """
            SELECT Transaction.amount, Transaction.created_at, VehicleAd.title, Photo.content AS photo_url
            FROM Transaction
            JOIN VehicleAd ON Transaction.ad_id = VehicleAd.ad_id
            LEFT JOIN Photo ON VehicleAd.vehicle_id = Photo.vehicle_id AND Photo.is_primary = TRUE
            WHERE Transaction.buyer_id = %s;
        """
        cursor.execute(bought_query, (user_id,))
        bought_transactions = cursor.fetchall()

        # Fetch transactions as seller
        sold_query = """
            SELECT Transaction.amount, Transaction.created_at, VehicleAd.title, Photo.content AS photo_url
            FROM Transaction
            JOIN VehicleAd ON Transaction.ad_id = VehicleAd.ad_id
            LEFT JOIN Photo ON VehicleAd.vehicle_id = Photo.vehicle_id AND Photo.is_primary = TRUE
            WHERE Transaction.seller_id = %s;
        """
        cursor.execute(sold_query, (user_id,))
        sold_transactions = cursor.fetchall()

        return render_template('transactions.html', bought=bought_transactions, sold=sold_transactions)

    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('auth_routes.dashboard'))

    finally:
        cursor.close()
        db.close()

