plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// Numer wersji aplikacji (APK). Zwiększ go w android/apk-version.txt tylko przy zmianach w kodzie Androida.
val apkVersion = rootProject.file("apk-version.txt").readText().trim().toInt()
// Adres GitHub Pages wstawia automatycznie workflow (np. https://login.github.io/my-hotdog)
val pagesUrl = (project.findProperty("pagesUrl") as String?) ?: ""

android {
    namespace = "pl.myhotdog.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "pl.myhotdog.app"
        minSdk = 24
        targetSdk = 34
        versionCode = apkVersion
        versionName = "1.$apkVersion"
        buildConfigField("String", "PAGES_URL", "\"$pagesUrl\"")
    }

    signingConfigs {
        create("hotdog") {
            storeFile = rootProject.file("keystore/myhotdog.jks")
            storePassword = "myhotdog123"
            keyAlias = "myhotdog"
            keyPassword = "myhotdog123"
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("hotdog")
        }
        debug {
            signingConfig = signingConfigs.getByName("hotdog")
        }
    }

    buildFeatures { buildConfig = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation("androidx.webkit:webkit:1.11.0")
}
