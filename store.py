from flask import Blueprint, render_template, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, PaymentLink, User

store_bp = Blueprint('store', __name__)

@store_bp.route('/store')
@login_required
def store():
    # Get all payment links ordered by amount
    payment_links = PaymentLink.query.order_by(PaymentLink.amount).all()
    
    # Highlight best deals
    featured_deals = PaymentLink.query.filter_by(is_featured=True).all()
    
    return render_template('store/store.html',
                         payment_links=payment_links,
                         featured_deals=featured_deals,
                         user=current_user)

@store_bp.route('/initialize-payment-links', methods=['POST'])
def initialize_payment_links():
    """Initialize default payment links with attractive bonuses"""
    try:
        # Clear existing links
        PaymentLink.query.delete()
        
        # Create new payment links with bonuses
        links = [
            PaymentLink(
                amount=5.00,
                paypal_link="https://www.paypal.com/ncp/payment/M2Y5B385X3AB8",
                bonus_amount=2.00,
                description="Quick Start: Get $7 for $5!",
                is_featured=False
            ),
            PaymentLink(
                amount=10.00,
                paypal_link="https://www.paypal.com/ncp/payment/LDA7E9DGCK5F6",
                bonus_amount=5.00,
                description="Popular: $10 + $5 BONUS!",
                is_featured=True
            ),
            PaymentLink(
                amount=15.00,
                paypal_link="https://www.paypal.com/ncp/payment/AHEUX4EYN8AHU",
                bonus_amount=7.50,
                description="Hot Deal: 50% Extra! Pay $15 Get $22.50",
                is_featured=True
            ),
            PaymentLink(
                amount=20.00,
                paypal_link="https://www.paypal.com/ncp/payment/QF5AF776D862J",
                bonus_amount=12.00,
                description="BEST VALUE: $20 + $12 FREE!",
                is_featured=True
            )
        ]
        
        for link in links:
            db.session.add(link)
            
        db.session.commit()
        return jsonify({"success": True, "message": "Payment links initialized"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})
