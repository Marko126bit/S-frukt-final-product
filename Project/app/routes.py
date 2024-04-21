# routes.py
from flask import  jsonify, render_template, request, url_for, flash, redirect, send_file
from sqlalchemy import func
from .forms import LoginForm,  PartnerForm
from .models import MainStorage, Partner,  SmallStorage, TransactionLog, User, Partner
from .extensions import db
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash
import pytz


def configure_routes(app):

    @app.route('/')
    def home():
        return render_template('home.html')

#log in system/////////////////////////////////////////////////////////////////////
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        
        form = LoginForm()
        if form.validate_on_submit():
            # Attempt to find the user by their username
            user = User.query.filter_by(username=form.username.data).first()
             # If a user is found and password matches
            if user and check_password_hash(user.password, form.password.data):
                login_user(user)
                flash('You have been logged in!', 'success')
                
                # If the user was trying to visit a page that requires login, redirect there
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('home'))
            else:
                flash('Login Unsuccessful. Please check username or password', 'danger')
        
        return render_template('login.html', title='Login', form=form)
        

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('home'))
    
   #logic for small and partner/////////////////////////////////////////////////
    @app.route('/adjust_main_storage', methods=['GET'])
    def adjust_main_storage_page():
     # Render the HTML page with context data
     return render_template('adjust_main_storage.html')


    @app.route('/partners', methods=['GET', 'POST'])
    def partners():
     form = PartnerForm()
     if form.validate_on_submit():
        partner = Partner(name=form.name.data, quantity=form.quantity.data)
        db.session.add(partner)
        db.session.commit()
        flash('New partner created!', 'success')
        return redirect(url_for('partners'))
    
     all_partners = Partner.query.all()
     partner_names = {partner.id: partner.name for partner in all_partners}

     return render_template('partners.html', form=form, partners=all_partners, partner_names=partner_names)

    @app.route('/create_small_storage', methods=['GET', 'POST'])
    def create_small_storage():
     if request.method == 'POST':
        name = request.form.get('name')
        quantity = int(request.form.get('quantity', 0))  # Default to 0 if quantity is not provided

        if name:
            # Retrieve the single instance of main storage
            main_storage = MainStorage.query.get(1)  # Assuming you have only one instance of MainStorage

            if main_storage and main_storage.quantity >= quantity:
                # Subtract the quantity from the main storage
                main_storage.quantity -= quantity

                # Create and add the new small storage
                new_small_storage = SmallStorage(name=name, quantity=quantity, main_storage_id=main_storage.id)
                db.session.add(new_small_storage)
                db.session.commit()

                flash('New small storage created!', 'success')
                return redirect(url_for('create_small_storage'))
            else:
                # Not enough quantity in main storage to create small storage
                flash('Not enough quantity in main storage!', 'error')
        else:
            # Name field is empty
            flash('Name is required!', 'error')

     # For a GET request or if there's an error, just render the create page
     small_storages = SmallStorage.query.all()
     return render_template('create_small_storage.html', small_storages=small_storages)




    
    #transfer logic ////////////////////////////////////////////////////////////
    @app.route('/get_main_storage_quantity', methods=['GET']) 
    def get_main_storage_quantity():
     main_storage = MainStorage.get_main_storage()
     if main_storage:
        return jsonify({'quantity': main_storage.quantity})
     else:
        return jsonify({'error': 'Main storage not found'}), 404

    @app.route('/get_entities_by_type')
    def get_entities_by_type():
     entity_type = request.args.get('type')
     if entity_type == 'partner':
        # Replace with actual database query to get partners
        partners = [{'name': 'Partner One'}, {'name': 'Partner Two'}]
        return jsonify(partners)
     elif entity_type == 'storage':
        # Replace with actual database query to get storages
        storages = [{'name': 'Storage One'}, {'name': 'Storage Two'}]
        return jsonify(storages)
     else:
        return jsonify({'error': 'Invalid entity type'}), 400
     
    @app.route('/api/partner_data')
    def api_partner_data():
     # Query for the main storage quantity
     main_storage = MainStorage.query.get(1)  # Assuming there's only one main storage entry
     main_storage_quantity = main_storage.quantity if main_storage else 0

    # Query for partner data
     partners = Partner.query.with_entities(Partner.name, Partner.quantity).all()
     # Serialize the data
     partner_data = [{'name': partner.name, 'quantity': partner.quantity} for partner in partners]

     # Add main storage to the partner data with a distinctive name
     partner_data.insert(0, {'name': 'Main Storage', 'quantity': main_storage_quantity})

     return jsonify(partner_data)
    
    @app.route('/process_transaction', methods=['POST'])
    def process_transaction():
     data = request.get_json()
     partner_id = data.get('partner_id')
     transaction_quantity = data.get('quantity')
     operation = data.get('operation')  # 'add' or 'subtract'

     main_storage = MainStorage.query.get(1)  # Assuming only one main storage
     partner = Partner.query.get(partner_id)

     if operation == 'add':
        # Add to main storage, subtract from partner
        main_storage.quantity += transaction_quantity
        partner.quantity -= transaction_quantity
     elif operation == 'subtract':
        # Subtract from main storage, add to partner
        main_storage.quantity -= transaction_quantity
        partner.quantity += transaction_quantity

     db.session.commit()

     # Return the updated quantities
     return jsonify({
        'main_storage_quantity': main_storage.quantity,
        'partner_name': partner.name,
        'partner_quantity': partner.quantity
     })



    @app.route('/adjust_main_storage', methods=['POST'])
    def adjust_main_storage():
     data = request.get_json()
     partner_id = data.get('partner_id')  # Ensure you're getting the partner's ID
     quantity = data.get('quantity')
     operation = data.get('operation')

    # Retrieve the single MainStorage instance and the Partner instance by ID
     main_storage = MainStorage.query.get(1)  # Assuming there's only one main storage instance
     partner = Partner.query.get(partner_id)

     if not main_storage or not partner:
        return jsonify({'error': 'Main storage or partner not found'}), 404

     if operation == 'add':
        # When adding to main storage, subtract the same quantity from the partner's storage
        if partner.quantity >= quantity:
            partner.quantity -= quantity
            main_storage.quantity += quantity
        else:
            return jsonify({'error': 'Partner does not have enough quantity to add to main storage'}), 400

     elif operation == 'subtract':
        # When subtracting from main storage, add the same quantity to the partner's storage
        if main_storage.quantity >= quantity:
            main_storage.quantity -= quantity
            partner.quantity += quantity
        else:
            return jsonify({'error': 'Not enough quantity in main storage to subtract'}), 400

     else:
        return jsonify({'error': 'Invalid operation'}), 400
     
      # Fetch the updated quantities for all partners and the main storage
     updated_partner_data = Partner.query.with_entities(Partner.id, Partner.name, Partner.quantity).all()
     main_storage_quantity = main_storage.quantity

     # Serialize the updated partner data
     updated_partner_list = [{'id': partner.id, 'name': partner.name, 'quantity': partner.quantity} for partner in updated_partner_data]

     # Commit the changes to the database
     db.session.commit()
     return jsonify({
        'message': 'Storage adjusted successfully',
        'new_main_storage_quantity': main_storage.quantity,
        'new_partner_quantity': partner.quantity
     })


    @app.route('/get_quantities')
    def get_quantities():
     main_storage = MainStorage.query.get(1)  # Assuming there's only one main storage instance
     partners = Partner.query.all()

     if not main_storage:
        return jsonify({'error': 'Main storage not found'}), 404

     partners_data = [{'id': partner.id, 'name': partner.name, 'quantity': partner.quantity} for partner in partners]

     return jsonify({
        'main_storage_quantity': main_storage.quantity,
        'partners': partners_data
     })

    @app.route('/get_small_storages', methods=['GET'])
    def get_small_storages():
     # Query all small storages and return their details
     small_storages = SmallStorage.query.all()
     storages_data = [{'id': storage.id, 'name': storage.name, 'quantity': storage.quantity} for storage in small_storages]
     return jsonify({'storages': storages_data})

    @app.route('/get_partners')
    def get_partners():
     partners = Partner.query.with_entities(Partner.id, Partner.name).all()
     partner_list = [{'id': partner.id, 'name': partner.name} for partner in partners]
     return jsonify(partner_list)
    

    @app.route('/adjust_small_storage', methods=['POST'])
    def adjust_small_storage():
     data = request.get_json()
     small_storage_id = data.get('small_storage_id')
     quantity = data.get('quantity')
     operation = data.get('operation')

    # Retrieve the small storage instance
     small_storage = SmallStorage.query.get(small_storage_id)
     # Retrieve the single MainStorage instance
     main_storage = MainStorage.query.get(1)  # Assuming there's only one main storage instance

     if not small_storage or not main_storage:
         return jsonify({'error': 'Small storage or main storage not found'}), 404

     if operation == 'add':
        # Ensure main_storage has enough quantity to deduct
        if main_storage.quantity >= quantity:
            main_storage.quantity -= quantity
            small_storage.quantity += quantity
        else:
            return jsonify({'error': 'Not enough quantity in main storage'}), 400
     elif operation == 'subtract':
        # Ensure small_storage has enough quantity to give back
        if small_storage.quantity >= quantity:
            small_storage.quantity -= quantity
            main_storage.quantity += quantity
        else:
            return jsonify({'error': 'Not enough quantity in small storage'}), 400
     else:
        return jsonify({'error': 'Invalid operation'}), 400

    # Commit the changes to the database
     db.session.commit()

     return jsonify({
        'message': 'Storage adjusted successfully',
        'new_main_storage_quantity': main_storage.quantity,
        'new_small_storage_quantity': small_storage.quantity
    })

    @app.route('/transaction_logs')
    def transaction_logs():
    # Fetch all logs
     logs = TransactionLog.query.order_by(TransactionLog.timestamp.desc()).all()

     # Fetch all partners and small storages for name resolution
     partners = {partner.id: partner.name for partner in Partner.query.all()}
     small_storages = {storage.id: storage.name for storage in SmallStorage.query.all()}

     # Define your local timezone
     local_tz = pytz.timezone('Europe/Berlin')  

     # Resolve names and convert timestamps
     for log in logs:
        if log.source_type == 'partner' and log.source_id in partners:
            log.source_name = partners[log.source_id]
        elif log.source_type == 'small_storage' and log.source_id in small_storages:
            log.source_name = small_storages[log.source_id]
        else:
            log.source_name = 'Main Storage'

        if log.destination_type == 'partner' and log.destination_id in partners:
            log.destination_name = partners[log.destination_id]
        elif log.destination_type == 'small_storage' and log.destination_id in small_storages:
            log.destination_name = small_storages[log.destination_id]
        else:
            log.destination_name = 'Main Storage'

        # Convert timestamp to local time zone
        log.local_timestamp = log.timestamp.replace(tzinfo=pytz.utc).astimezone(local_tz)

     return render_template('transaction_logs.html', logs=logs)

    @app.route('/delete_all_transactions', methods=['DELETE'])
    def delete_all_transactions():
     # Delete all transactions
     TransactionLog.query.delete()
     db.session.commit()
     return jsonify({'message': 'All transactions deleted successfully'})
    
    @app.route('/sort_transactions_by_day')
    def sort_transactions_by_day():
     # Fetch transactions sorted by day
     sorted_logs = db.session.query(
        TransactionLog.id,
        TransactionLog.action_type,
        # ... (other fields) ...
        TransactionLog.timestamp
     ).order_by(func.date(TransactionLog.timestamp).desc()).all()

     # Convert timestamps to local time zone
     local_tz = pytz.timezone('Europe/Berlin')  # replace 'Your_Timezone' with your time zone
     for log in sorted_logs:
        log.timestamp = log.timestamp.replace(tzinfo=pytz.utc).astimezone(local_tz)

     return jsonify(sorted_logs)
#////////////////////edit delete add//////////////////////////////////////////////


    @app.route('/partner/edit/<int:partner_id>', methods=['POST'])
    def edit_partner(partner_id):
     partner = Partner.query.get_or_404(partner_id)
     name = request.form.get('name')
     quantity = request.form.get('quantity', type=int)

     if name:
         partner.name = name
     if quantity is not None:  # Check for `None` because `0` is a valid quantity
        partner.quantity = quantity
     db.session.commit()

     return jsonify({'success': 'Partner updated', 'partner_id': partner.id, 'name': partner.name, 'quantity': partner.quantity})

    
    @app.route('/partner/delete/<int:partner_id>', methods=['POST'])
    def delete_partner(partner_id):
     partner = Partner.query.get_or_404(partner_id)
     db.session.delete(partner)
     db.session.commit()
     return jsonify({'success': 'Partner deleted', 'partner_id': partner_id}
                    )
    
    @app.route('/partner/delete_all', methods=['POST']) 
    def delete_all_partners():
     Partner.query.delete()
     db.session.commit()
     return jsonify({'success': 'All partners deleted'})
    
    

    @app.route('/edit_small_storage', methods=['POST'])
    def edit_small_storage():
     data = request.get_json()
     small_storage_id = data['id']
     new_name = data.get('name', '').strip()  # Default to empty string if name is not provided
     new_quantity = data.get('quantity', None)  # Default to None if quantity is not provided

     small_storage = SmallStorage.query.get(small_storage_id)
     main_storage = MainStorage.query.get(1)  # Assuming there's only one main storage

     if small_storage and main_storage:
        # Initialize a flag to check if we need to update the main storage quantity
        update_main_storage = False

        # Update the name only if a new name was provided and it is different
        if new_name and new_name != small_storage.name:
            small_storage.name = new_name

        # Update the quantity only if a new quantity was provided and it is different
        if new_quantity is not None:
            new_quantity = int(new_quantity)
            if new_quantity != small_storage.quantity:
                # Calculate the quantity difference
                quantity_difference = new_quantity - small_storage.quantity

                # Check if there is enough in the main storage to accommodate the change
                if main_storage.quantity >= quantity_difference:
                    main_storage.quantity -= quantity_difference
                    small_storage.quantity = new_quantity
                    update_main_storage = True
                else:
                    return jsonify({'error': 'Not enough quantity in main storage'}), 400

        # Commit changes to the database only if there are changes to commit
        if new_name or update_main_storage:
            db.session.commit()
            return jsonify({'success': 'Storage updated successfully'})
        else:
            # If there are no changes, no need to commit and we return a message
            return jsonify({'success': 'No changes made to storage'})

     else:
        return jsonify({'error': 'Storage not found'}), 404


    @app.route('/delete_small_storage', methods=['POST'])
    def delete_small_storage():
     data = request.get_json()
     small_storage_id = data['id']
    
     small_storage = SmallStorage.query.get(small_storage_id)
     main_storage = MainStorage.query.get(1)  # Assuming there's only one main storage
    
     if small_storage and main_storage:
        main_storage.quantity += small_storage.quantity
        db.session.delete(small_storage)
        db.session.commit()
        return jsonify({'success': 'Storage deleted successfully'})
     else:
        return jsonify({'error': 'Storage not found'}), 404

    @app.route('/delete_all_small_storages', methods=['POST'])
    def delete_all_small_storages():
     main_storage = MainStorage.query.get(1)  # Assuming there's only one main storage
    
     if main_storage:
        small_storages = SmallStorage.query.all()
        for storage in small_storages:
            main_storage.quantity += storage.quantity
        num_rows_deleted = db.session.query(SmallStorage).delete()
        db.session.commit()
        return jsonify({'success': f'{num_rows_deleted} storages deleted successfully'})
     else:
        return jsonify({'error': 'Main storage not found'}),  

    @app.route('/profile/<int:partner_id>')
    def profile(partner_id):
    # Fetch partner details from the database using the provided partner_id
     partner = Partner.query.get_or_404(partner_id)
     return render_template('profile.html', partner=partner)