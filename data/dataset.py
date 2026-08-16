import pandas as pd

def get_training_data() -> pd.DataFrame:
    """Returns the hardcoded training dataset (both relevant and noise examples)."""
    
    data = [
        # RELEVANT JOBS = 1
        ("We are hiring a Flutter Developer with experience in Dart and Firebase.", 1),
        ("Looking for a Flutter engineer to develop cross platform mobile applications.", 1),
        ("Mobile Application Developer required with Flutter and Dart experience.", 1),
        ("We need a Flutter developer with REST API and Firebase knowledge.", 1),
        ("Hiring Mobile App Developer for Android and iOS application development.", 1),
        ("Flutter Developer position available. Experience with GetX is preferred.", 1),
        ("Looking for a Mobile Application Engineer with Flutter experience.", 1),
        ("We are looking for a Dart and Flutter developer to join our mobile team.", 1),
        ("Senior Flutter Developer required for a cross platform mobile application.", 1),
        ("Junior Flutter Developer wanted. Knowledge of Firebase and REST APIs required.", 1),
        ("Mobile developer needed with experience in Flutter, Dart and Git.", 1),
        ("We are hiring a Flutter engineer for our mobile application team.", 1),
        ("Flutter developer vacancy. Experience with API integration is required.", 1),
        ("Mobile app development role using Flutter and Dart.", 1),
        ("Looking for an Android and iOS developer with Flutter experience.", 1),
        ("Flutter developer required for remote mobile application project.", 1),
        ("Hiring a mobile application developer familiar with Flutter and Firebase.", 1),
        ("We need a cross-platform developer with Flutter and Dart skills.", 1),
        ("Mobile Engineer position. Flutter experience is highly preferred.", 1),
        ("Flutter Developer job opening with REST API integration responsibilities.", 1),
        # Kotlin / Android
        ("We are hiring a Kotlin Developer for native Android app development.", 1),
        ("Android Developer needed with Kotlin and Jetpack Compose experience.", 1),
        ("Kotlin Android Engineer required for our mobile product team.", 1),
        ("We are looking for an Android Engineer with Kotlin and MVVM experience.", 1),
        ("Junior Android Developer wanted. Kotlin and Android SDK experience required.", 1),
        # React Native
        ("React Native Developer required for cross-platform mobile app.", 1),
        ("We need a React Native Engineer experienced with JavaScript and mobile development.", 1),
        ("Mobile Developer position open. React Native and Expo experience preferred.", 1),
        ("Hiring React Native developer for iOS and Android application.", 1),

        # IRRELEVANT JOBS = 0
        ("We are hiring a Python Backend Developer with Django experience.", 0),
        ("Looking for a Java developer with Spring Boot experience.", 0),
        ("Marketing Executive required for our company.", 0),
        ("We are hiring an HR Manager with recruitment experience.", 0),
        ("Accountant needed with experience in financial reporting.", 0),
        ("Sales Executive position available in Dhaka.", 0),
        ("Looking for a UI UX Designer with Figma experience.", 0),
        ("Senior PHP developer required for Laravel project.", 0),
        ("DevOps Engineer wanted with AWS and Kubernetes experience.", 0),
        ("Data Analyst required with Excel and Power BI skills.", 0),
        ("Graphic Designer required for our creative team.", 0),
        ("Business Development Executive wanted.", 0),
        ("Content Writer required for our marketing department.", 0),
        ("Java Backend Engineer needed for enterprise application.", 0),
        ("Machine Learning Engineer required with Python experience.", 0),
        ("Project Manager wanted with Agile experience.", 0),
        ("Network Engineer required for our IT department.", 0),
        ("Customer Support Executive position available.", 0),
        ("Software QA Engineer required for testing team.", 0),
        ("Database Administrator wanted with PostgreSQL experience.", 0),
    ]

    noise_data = [
        ("Your Meghna Bank card transaction was completed successfully.", 0),
        ("Your one-time verification code is 35981. Do not share this code.", 0),
        ("Rafat, check out these Pins picked just for you.", 0),
        ("New recommendations based on your recent activity.", 0),
        ("Your OTP for login is 482910. Valid for 5 minutes.", 0),
        ("Your monthly bank statement is now available.", 0),
        ("Someone viewed your LinkedIn profile this week.", 0),
        ("Your package has been shipped and is on its way.", 0),
        ("Reminder: your subscription renews tomorrow.", 0),
        ("Security alert: new sign-in to your account detected.", 0),
        ("Your Telegram login code is 118273.", 0),
        ("Flash sale! 50% off everything this weekend only.", 0),
        ("Your electricity bill payment was successful.", 0),
        ("You have a new notification on Facebook.", 0),
        ("Complete your profile to get better recommendations.", 0),
    ]

    df = pd.DataFrame(data + noise_data, columns=["email_text", "label"])
    return df
