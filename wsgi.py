import click, pytest, sys
from flask.cli import with_appcontext, AppGroup

from datetime import datetime, timedelta
from App.database import db, get_migrate
from App.models import User, Driver, Drive, Street, Resident, StopRequest   
from App.main import create_app
from App.controllers import ( create_user, get_all_users_json, get_all_users, initialize )

# This commands file allow you to create convenient CLI commands for testing controllers

app = create_app()
migrate = get_migrate(app)

# This command creates and initializes the database
@app.cli.command("init", help="Creates and initializes the database")
def init():
    # Initialize database (drops and recreates all tables, creates bob user)
    initialize()
    
    # Create additional users
    sally = User(username='sally', password='sallypass')
    rob = User(username='rob', password='robpass')
    db.session.add_all([sally, rob])
    db.session.commit()
    
    # Get the bob user that was created by initialize()
    bob = User.query.filter_by(username='bob').first()
    
    # Create preset streets
    rye_street = Street(name='Rye')
    sourdough_street = Street(name='Sourdough')
    db.session.add_all([rye_street, sourdough_street])
    db.session.commit()
    
    # Make bob a driver
    bob_driver = Driver(user_id=bob.id, status='EN_ROUTE', location='Garage')
    db.session.add(bob_driver)
    db.session.commit()
    
    # Make sally a resident of Rye
    sally_resident = Resident(user_id=sally.id, street_id=rye_street.id, address='67 Brioche')
    db.session.add(sally_resident)
    db.session.commit()
    
    # Create bob's drives
    now = datetime.utcnow()
    two_hours_later = now + timedelta(hours=2)
    tomorrow_9am = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    drive_rye = Drive(
        driver_id=bob_driver.id,
        street_id=rye_street.id,
        arrive_at=two_hours_later,
        status='SCHEDULED'
    )
    
    drive_sourdough = Drive(
        driver_id=bob_driver.id,
        street_id=sourdough_street.id,
        arrive_at=tomorrow_9am,
        status='SCHEDULED'
    )
    
    db.session.add_all([drive_rye, drive_sourdough])
    db.session.commit()
    
    # Create sally's stop request for the Rye drive
    sally_stop_request = StopRequest(
        drive_id=drive_rye.id,
        resident_id=sally_resident.id,
        address='67 Brioche',
        status='PENDING'
    )
    db.session.add(sally_stop_request)
    db.session.commit()
    
    print('Database initialized with preloaded data:')
    print('- Users: sally, rob, bob')
    print('- Streets: Rye, Sourdough')
    print('- Bob is a driver with 2 scheduled drives')
    print('- Sally is a resident of Rye at 67 Brioche')
    print('- Sally has 1 stop request for the Rye drive')

'''
User Commands
'''

# Commands can be organized using groups

# create a group, it would be the first argument of the comand
# eg : flask user <command>
user_cli = AppGroup('user', help='User object commands') 

# Then define the command and any parameters and annotate it with the group (@)
@user_cli.command("create", help="Creates a user")
@click.argument("username", default="rob")
@click.argument("password", default="robpass")
def create_user_command(username, password):
    create_user(username, password)
    print(f'{username} created!')

# this command will be : flask user create bob bobpass

@user_cli.command("list", help="Lists users in the database")
@click.argument("format", default="string")
def list_user_command(format):
    if format == 'string':
        print(get_all_users())
    else:
        print(get_all_users_json())

app.cli.add_command(user_cli) # add the group to the cli

'''
Test Commands
'''

test = AppGroup('test', help='Testing commands') 

@test.command("user", help="Run User tests")
@click.argument("type", default="all")
def user_tests_command(type):
    if type == "unit":
        sys.exit(pytest.main(["-k", "UserUnitTests"]))
    elif type == "int":
        sys.exit(pytest.main(["-k", "UserIntegrationTests"]))
    else:
        sys.exit(pytest.main(["-k", "App"]))
    

app.cli.add_command(test)

# ----------- SIMPLE SETUP COMMANDS (print/input; no app groups) -----------
def _bv_prompt_nonempty(label: str) -> str:
    while True:
        s = input(f"{label}: ").strip()
        if s:
            return s
        print("Value required.")

@app.cli.command("create-driver")
def create_driver_cmd():
    """
    Create a driver profile attached to an existing user.
    """
    print("\n== Create Driver ==")
    users = User.query.order_by(User.id.asc()).all()
    if not users:
        print("No users exist yet.")
        if input("Create a user now? [y/N]: ").strip().lower() in ("y", "yes"):
            # call the other command inline
            create_user_cmd()
            users = User.query.order_by(User.id.asc()).all()
        else:
            print("Aborting.")
            return

    # show users
    for u in users:
        print(f"  {u.id}) {getattr(u, 'username', '(no username)')}")

    while True:
        raw = input("Enter user id to make a driver (or 0 to cancel): ").strip()
        if raw.isdigit():
            uid = int(raw)
            if uid == 0:
                print("Cancelled.")
                return
            user = User.query.get(uid)
            if user:
                break
        print("Invalid id. Try again.")

    # ensure this user doesn't already have a driver row
    existing = Driver.query.filter_by(user_id=user.id).first()
    if existing:
        print(f"User #{user.id} already has Driver #{existing.id}.")
        return

    d = Driver(user_id=user.id)  # defaults: OFF_DUTY, empty location
    db.session.add(d)
    db.session.commit()
    print(f"OK: created Driver #{d.id} for User #{user.id} ({getattr(user, 'username','')})")

@app.cli.command("create-street")
def create_street_cmd():
    """
    Create a street.
    """
    print("\n== Create Street ==")
    name = _bv_prompt_nonempty("Street name")
    # unique by name (case-insensitive)
    exists = Street.query.filter(db.func.lower(Street.name) == name.lower()).first()
    if exists:
        print(f"Error: street '{name}' already exists (#{exists.id}).")
        return
    st = Street(name=name)
    db.session.add(st)
    db.session.commit()
    print(f"OK: created Street #{st.id} ({st.name})")

@app.cli.command("list-drivers")
def list_drivers_cmd():
    drivers = Driver.query.order_by(Driver.id.asc()).all()
    if not drivers:
        print("No drivers.")
        return
    for d in drivers:
        uname = getattr(getattr(d, "user", None), "username", "(no user)")
        print(f"Driver #{d.id} user:{d.user_id} ({uname}) status:{d.status} loc:{d.location}")

@app.cli.command("list-streets")
def list_streets_cmd():
    streets = Street.query.order_by(Street.id.asc()).all()
    if not streets:
        print("No streets.")
        return
    for s in streets:
        print(f"Street #{s.id} {s.name}")


# ------- DRIVER: Schedule a Drive (menu-driven, using print/input) -------

def _pick_from_menu(rows, label, show=lambda r: str(r)):
    """
    Simple numeric menu using print/input. Returns the chosen row or None.
    """
    if not rows:
        print(f"No {label} found.")
        return None
    print(f"\nSelect {label}:")
    for i, r in enumerate(rows, start=1):
        print(f"  {i}) {show(r)}")
    while True:
        raw = input("Enter number (or 0 to cancel): ").strip()
        if raw.isdigit():
            choice = int(raw)
            if choice == 0:
                return None
            if 1 <= choice <= len(rows):
                return rows[choice - 1]
        print("Invalid choice. Try again.")

def _yes_no(prompt: str) -> bool:
    while True:
        ans = input(f"{prompt} [y/n]: ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'.")

def _parse_dt(s: str):
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        return None

@app.cli.command("schedule-drive")
def schedule_drive_cmd():
    """
    (Driver) Schedule a drive to a street — interactive, using print/input.
      1) choose a Driver
      2) choose/create a Street
      3) enter arrival datetime (YYYY-MM-DD HH:MM)
      4) save Drive
    """
    # 1) Pick Driver
    drivers = Driver.query.order_by(Driver.id.asc()).all()
    if not drivers:
        print("No drivers exist. Create a driver/user first, then retry.")
        return
    chosen_driver = _pick_from_menu(
        drivers,
        "driver",
        show=lambda d: f"Driver #{d.id} - {getattr(d.user, 'username', '(no user)')} [{d.status}]"
    )
    if not chosen_driver:
        print("Cancelled.")
        return

    # 2) Pick/Create Street
    streets = Street.query.order_by(Street.name.asc()).all()
    if not streets:
        print("\nNo streets exist.")
        if _yes_no("Create a new street now?"):
            name = input("Street name: ").strip()
            if not name:
                print("Street name is required. Aborting.")
                return
            st = Street(name=name)
            db.session.add(st)
            db.session.commit()
            streets = [st]
        else:
            print("Aborting (no streets).")
            return

    chosen_street = _pick_from_menu(streets, "street", show=lambda s: f"{s.name} (#{s.id})")
    if not chosen_street:
        print("Cancelled.")
        return

    # 3) Arrival time
    print("\nEnter arrival in format YYYY-MM-DD HH:MM (24h). Example: 2025-10-02 09:30")
    while True:
        s = input("Arrival datetime: ").strip()
        arrive_at = _parse_dt(s)
        if not arrive_at:
            print("Invalid format. Try again.")
            continue
        if arrive_at <= datetime.utcnow():
            print("Arrival must be in the future.")
            continue
        break

    # 4) Save Drive
    drive = Drive(driver_id=chosen_driver.id, street_id=chosen_street.id, arrive_at=arrive_at)
    db.session.add(drive)
    db.session.commit()
    print(f"\nOK: Drive #{drive.id} scheduled for {chosen_street.name} at {arrive_at} by Driver #{chosen_driver.id}.")

# ========= RESIDENT: set home street + view inbox =========


def _choose_user_res(prompt="Pick user"):
    users = User.query.order_by(User.id.asc()).all()
    if not users:
        print("No users exist. Run: flask user create <name> <pass>")
        return None
    print(f"\n{prompt}:")
    for u in users:
        print(f"  {u.id}) {getattr(u,'username','(no username)')}")
    while True:
        raw = input("User id (0 to cancel): ").strip()
        if raw.isdigit():
            uid = int(raw)
            if uid == 0:
                return None
            u = User.query.get(uid)
            if u:
                return u
        print("Invalid id. Try again.")

def _choose_driver(prompt="Pick driver"):
    drivers = Driver.query.order_by(Driver.id.asc()).all()
    if not drivers:
        print("No drivers exist. Create a driver first.")
        return None
    return _pick_from_menu(
        drivers,
        "driver",
        show=lambda d: f"Driver #{d.id} - {getattr(d.user, 'username', '(no user)')} [{d.status}]"
    )

@app.cli.command("set-resident-street")
def set_resident_street_cmd():
    """
    Attach a non-driver user to a home street (used by resident-inbox).
    """
    user = _choose_user_res("Pick user to set as resident")
    if not user:
        print("Cancelled."); return

    # Treat user as Resident if they don't have a Driver profile
    drv = Driver.query.filter_by(user_id=user.id).first()
    if drv:
        print(f"User #{user.id} is a Driver (Driver #{drv.id}); choose a non-driver user.")
        return

    streets = Street.query.order_by(Street.name.asc()).all()
    if not streets:
        print("No streets exist. Run: flask create-street")
        return
    st = _pick_from_menu(streets, "street", show=lambda s: f"{s.name} (#{s.id})")
    if not st:
        print("Cancelled."); return

    res = Resident.query.filter_by(user_id=user.id).first()
    if res:
        res.street_id = st.id
        db.session.commit()
        print(f"OK: Updated resident User #{user.id} to street '{st.name}'.")
    else:
        # Prompt for address
        address = input("Enter address for this resident: ").strip()
        if not address:
            print("Address is required. Cancelled.")
            return
        res = Resident(user_id=user.id, street_id=st.id, address=address)
        db.session.add(res)
        db.session.commit()
        print(f"OK: Set resident User #{user.id} to street '{st.name}' (Resident #{res.id}).")

@app.cli.command("resident-inbox")
def resident_inbox_cmd():
    """
    (Resident) View inbox for scheduled drives to their street.
    A user is a resident if they do NOT have a Driver profile.
    """
    user = _choose_user_res("Pick resident user to view inbox")
    if not user:
        print("Cancelled."); return

    drv = Driver.query.filter_by(user_id=user.id).first()
    if drv:
        print(f"User #{user.id} is a Driver (Driver #{drv.id}). Choose a non-driver user.")
        return

    res = Resident.query.filter_by(user_id=user.id).first()
    if not res:
        print("This user has no home street set. Run: flask set-resident-street")
        return

    street = Street.query.get(res.street_id)
    if not street:
        print("Resident street not found. Set it again with: flask set-resident-street")
        return

    now = datetime.utcnow()
    drives = (Drive.query
                    .filter(Drive.street_id == street.id, Drive.arrive_at >= now)
                    .order_by(Drive.arrive_at.asc())
                    .all())

    print(f"\nUpcoming drives for {street.name}:")
    if not drives:
        print("  (none)")
        return
    for d in drives:
        print(f"  - Drive #{d.id} at {d.arrive_at} (driver {d.driver_id})")

# ========= RESIDENT: request a stop (print/input) =========

@app.cli.command("resident-request-stop")
def resident_request_stop_cmd():
    """
    (Resident) Request a stop on an upcoming drive for their street.
    Steps:
      1) pick a resident user (must NOT be a driver)
      2) choose one upcoming drive on that resident's street
      3) enter address
      4) save request with status=PENDING
    """

    # 1) choose resident user
    user = _choose_user_res("Pick resident user to request a stop")
    if not user:
        print("Cancelled."); return

    drv = Driver.query.filter_by(user_id=user.id).first()
    if drv:
        print(f"User #{user.id} is a Driver (Driver #{drv.id}). Choose a non-driver user.")
        return

    res = Resident.query.filter_by(user_id=user.id).first()
    if not res:
        print("This user has no home street set. Run: flask set-resident-street")
        return

    street = Street.query.get(res.street_id)
    if not street:
        print("Resident street not found. Set it again with: flask set-resident-street")
        return

    # 2) list upcoming drives on that street
    now = datetime.utcnow()
    drives = (Drive.query
                    .filter(Drive.street_id == street.id, Drive.arrive_at >= now)
                    .order_by(Drive.arrive_at.asc())
                    .all())
    if not drives:
        print(f"No upcoming drives for {street.name}."); return

    chosen_drive = _pick_from_menu(
        drives,
        "upcoming drive",
        show=lambda d: f"Drive #{d.id} at {d.arrive_at} (driver {d.driver_id})"
    )
    if not chosen_drive:
        print("Cancelled."); return

    # 3) capture address
    while True:
        address = input("Pickup address / landmark: ").strip()
        if address:
            break
        print("Address is required.")

    # 4) save
    req = StopRequest(
        drive_id=chosen_drive.id,
        resident_id=res.id,
        address=address,
        status="PENDING",
    )
    db.session.add(req)
    db.session.commit()

    print(f"OK: Stop request #{req.id} recorded for Drive #{chosen_drive.id} on {street.name} (status PENDING).")

# ========= DRIVER: status management and request handling =========

@app.cli.command("driver-set-status")
def driver_set_status_cmd():
    """
    (Driver) Update driver status and location.
    """
    print("\n== Driver Status Update ==")
    
    # Choose driver
    chosen_driver = _choose_driver("Pick driver to update status")
    if not chosen_driver:
        print("Cancelled.")
        return
    
    # Choose new status
    statuses = ["OFF_DUTY", "EN_ROUTE", "DELAYED", "ACCEPTED", "REJECTED", "COMPLETED"]
    print("\nSelect new status:")
    for i, status in enumerate(statuses, 1):
        print(f"  {i}) {status}")
    
    while True:
        raw = input("Enter status number (or 0 to cancel): ").strip()
        if raw.isdigit():
            choice = int(raw)
            if choice == 0:
                print("Cancelled.")
                return
            if 1 <= choice <= len(statuses):
                new_status = statuses[choice - 1]
                break
        print("Invalid choice. Try again.")
    
    # Update location
    new_location = input(f"Enter location (current: {chosen_driver.location}): ").strip()
    if not new_location:
        new_location = chosen_driver.location
    
    # Update driver
    chosen_driver.status = new_status
    chosen_driver.location = new_location
    chosen_driver.status_updated_at = datetime.utcnow()
    db.session.commit()
    
    print(f"OK: Driver #{chosen_driver.id} status updated to {new_status} at {new_location}.")

@app.cli.command("driver-requests")
def driver_requests_cmd():
    """
    (Driver) View all stop requests for a driver's upcoming drives.
    """
    print("\n== Driver Stop Requests ==")
    
    # Choose driver
    chosen_driver = _choose_driver("Pick driver to view requests")
    if not chosen_driver:
        print("Cancelled.")
        return
    
    # Get upcoming drives for this driver
    now = datetime.utcnow()
    upcoming_drives = Drive.query.filter(
        Drive.driver_id == chosen_driver.id,
        Drive.arrive_at >= now
    ).order_by(Drive.arrive_at.asc()).all()
    
    if not upcoming_drives:
        print(f"No upcoming drives for Driver #{chosen_driver.id}.")
        return
    
    print(f"\nUpcoming drives for Driver #{chosen_driver.id}:")
    total_requests = 0
    
    for drive in upcoming_drives:
        street = Street.query.get(drive.street_id)
        requests = StopRequest.query.filter_by(drive_id=drive.id).all()
        total_requests += len(requests)
        
        print(f"\nDrive #{drive.id} to {street.name} at {drive.arrive_at}")
        if requests:
            for req in requests:
                resident = Resident.query.get(req.resident_id)
                user = User.query.get(resident.user_id)
                print(f"  - Request #{req.id}: {user.username} at {req.address}")
                print(f"    Status: {req.status}")
        else:
            print("  (no stop requests)")
    
    print(f"\nTotal stop requests: {total_requests}")

@app.cli.command("driver-update-request")
def driver_update_request_cmd():
    """
    (Driver) Update the status of a stop request.
    """
    print("\n== Update Stop Request Status ==")
    
    # Choose driver
    chosen_driver = _choose_driver("Pick driver to update requests")
    if not chosen_driver:
        print("Cancelled.")
        return
    
    # Get all pending requests for this driver's upcoming drives
    now = datetime.utcnow()
    upcoming_drives = Drive.query.filter(
        Drive.driver_id == chosen_driver.id,
        Drive.arrive_at >= now
    ).all()
    
    if not upcoming_drives:
        print(f"No upcoming drives for Driver #{chosen_driver.id}.")
        return
    
    # Collect all requests
    all_requests = []
    for drive in upcoming_drives:
        requests = StopRequest.query.filter_by(drive_id=drive.id).all()
        for req in requests:
            resident = Resident.query.get(req.resident_id)
            user = User.query.get(resident.user_id)
            street = Street.query.get(drive.street_id)
            all_requests.append((req, user, street, drive))
    
    if not all_requests:
        print(f"No stop requests found for Driver #{chosen_driver.id}.")
        return
    
    # Choose request to update
    print(f"\nSelect request to update:")
    for i, (req, user, street, drive) in enumerate(all_requests, 1):
        print(f"  {i}) Request #{req.id}: {user.username} at {req.address}")
        print(f"     Drive #{drive.id} to {street.name} at {drive.arrive_at}")
        print(f"     Current status: {req.status}")
    
    while True:
        raw = input("Enter request number (or 0 to cancel): ").strip()
        if raw.isdigit():
            choice = int(raw)
            if choice == 0:
                print("Cancelled.")
                return
            if 1 <= choice <= len(all_requests):
                selected_req, selected_user, selected_street, selected_drive = all_requests[choice - 1]
                break
        print("Invalid choice. Try again.")
    
    # Choose new status
    statuses = ["PENDING", "CONFIRMED", "CANCELLED", "COMPLETED"]
    print(f"\nCurrent status: {selected_req.status}")
    print("Select new status:")
    for i, status in enumerate(statuses, 1):
        print(f"  {i}) {status}")
    
    while True:
        raw = input("Enter status number (or 0 to cancel): ").strip()
        if raw.isdigit():
            choice = int(raw)
            if choice == 0:
                print("Cancelled.")
                return
            if 1 <= choice <= len(statuses):
                new_status = statuses[choice - 1]
                break
        print("Invalid choice. Try again.")
    
    # Update request
    selected_req.status = new_status
    db.session.commit()
    
    print(f"OK: Request #{selected_req.id} status updated to {new_status}.")

@app.cli.command("resident-request-status")
def resident_request_status_cmd():
    """
    (Resident) View status of stop requests for a resident.
    """
    print("\n== Resident Request Status ==")
    
    # Choose resident user
    user = _choose_user_res("Pick resident user to view request status")
    if not user:
        print("Cancelled.")
        return
    
    # Check if user is a driver
    drv = Driver.query.filter_by(user_id=user.id).first()
    if drv:
        print(f"User #{user.id} is a Driver (Driver #{drv.id}). Choose a non-driver user.")
        return
    
    # Get resident
    res = Resident.query.filter_by(user_id=user.id).first()
    if not res:
        print("This user has no home street set. Run: flask set-resident-street")
        return
    
    # Get all stop requests for this resident
    requests = StopRequest.query.filter_by(resident_id=res.id).order_by(StopRequest.requested_at.desc()).all()
    
    if not requests:
        print(f"No stop requests found for {user.username}.")
        return
    
    print(f"\nStop requests for {user.username} (Resident #{res.id}):")
    for req in requests:
        drive = Drive.query.get(req.drive_id)
        street = Street.query.get(drive.street_id)
        driver = Driver.query.get(drive.driver_id)
        driver_user = User.query.get(driver.user_id)
        
        print(f"\nRequest #{req.id}:")
        print(f"  Drive: #{drive.id} to {street.name} at {drive.arrive_at}")
        print(f"  Driver: {driver_user.username} (Driver #{driver.id})")
        print(f"  Address: {req.address}")
        print(f"  Status: {req.status}")
        print(f"  Requested: {req.requested_at}")


