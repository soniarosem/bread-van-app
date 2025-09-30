📋 MASTER LIST OF CLI COMMANDS

Here's the complete list of all available CLI commands for the Bread Van App:


🔧 Setup & Initialization

flask init - Creates and initializes the database with preloaded data

flask db - Perform database migrations


👥 User Management

flask user create [username] [password] - Creates a new user

flask user list [format] - Lists all users (string or json format)


🚗 Driver Commands

flask create-driver - Create a driver profile for an existing user

flask list-drivers - List all drivers with their status and location

flask driver-set-status - Update driver status (OFF_DUTY, EN_ROUTE, DELAYED, ACCEPTED, REJECTED, COMPLETED) and location

flask driver-requests - View all stop requests for a driver's upcoming drives

flask driver-update-request - Update the status of a stop request (PENDING, CONFIRMED, CANCELLED, COMPLETED)

flask schedule-drive - Schedule a new drive to a street

🏠 Resident Commands

flask set-resident-street - Set a user as a resident of a specific street

flask resident-inbox - View upcoming drives for a resident's street

flask resident-request-stop - Request a stop on an upcoming drive

flask resident-request-status - View status of all stop requests for a resident


🛣️ Street Management

flask create-street - Create a new street

flask list-streets - List all streets


🧪 Testing

flask test user [type] - Run user tests (unit, int, or all)


🔧 Development

flask run - Run the development server

flask shell - Open a Python shell with app context

flask routes - Show all available routes


📊 Current Preloaded Data:

Users: sally, rob, bob

Streets: Rye, Sourdough

Bob: Driver with EN_ROUTE status, 2 scheduled drives

Sally: Resident of Rye at "67 Brioche" with 1 stop request


Happy bread buying! 🎉
