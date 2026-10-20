package pl.myhotdog.app

import android.annotation.SuppressLint
import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.webkit.WebViewAssetLoader
import org.json.JSONObject
import java.io.File
import java.io.FileInputStream
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

/**
 * My hotdog – gra działa w WebView.
 * Pliki gry są w assets/www (wbudowane w APK). Przy starcie aplikacja sprawdza
 * GitHub Pages: jeśli jest nowsza wersja gry, pobiera ją do pamięci telefonu
 * i od razu jej używa. Zapis gry (localStorage) zostaje, bo adres strony się nie zmienia.
 */
class MainActivity : Activity() {

    private lateinit var web: WebView
    private val host = "appassets.androidplatform.net"

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = 0xFFD8EFE9.toInt()

        val loader = WebViewAssetLoader.Builder()
            .setDomain(host)
            .addPathHandler("/www/", WwwHandler())
            .build()

        web = WebView(this)
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.mediaPlaybackRequiresUserGesture = false
        web.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? =
                loader.shouldInterceptRequest(request.url)

            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                if (request.url.host == host) return false
                startActivity(Intent(Intent.ACTION_VIEW, request.url))
                return true
            }
        }
        setContentView(web)
        web.loadUrl("https://$host/www/index.html")
    }

    /** Najpierw pliki pobrane z GitHub Pages, a jeśli ich nie ma – te wbudowane w APK. */
    inner class WwwHandler : WebViewAssetLoader.PathHandler {
        override fun handle(path: String): WebResourceResponse? {
            if (path.contains("..")) return null
            val f = File(filesDir, "www/$path")
            val stream = try {
                if (f.isFile) FileInputStream(f) else assets.open("www/$path")
            } catch (e: IOException) {
                return null
            }
            val mime = when {
                path.endsWith(".html") -> "text/html"
                path.endsWith(".js") -> "application/javascript"
                path.endsWith(".json") -> "application/json"
                path.endsWith(".css") -> "text/css"
                path.endsWith(".png") -> "image/png"
                path.endsWith(".svg") -> "image/svg+xml"
                else -> "application/octet-stream"
            }
            return WebResourceResponse(mime, "utf-8", stream).apply {
                responseHeaders = mapOf("Cache-Control" to "no-cache")
            }
        }
    }

    private fun localVersion(): Int {
        return try {
            val f = File(filesDir, "www/version.json")
            val txt = if (f.isFile) f.readText() else assets.open("www/version.json").bufferedReader().use { it.readText() }
            JSONObject(txt).optInt("web", 0)
        } catch (e: Exception) { 0 }
    }

    private fun httpGet(url: String): ByteArray {
        val c = URL(url).openConnection() as HttpURLConnection
        c.connectTimeout = 8000
        c.readTimeout = 20000
        c.useCaches = false
        c.setRequestProperty("Cache-Control", "no-cache")
        try {
            if (c.responseCode != 200) throw IOException("HTTP " + c.responseCode)
            return c.inputStream.use { it.readBytes() }
        } finally {
            c.disconnect()
        }
    }

    @Volatile private var checking = false

    private fun checkUpdates() {
        val base = BuildConfig.PAGES_URL.trimEnd('/')
        if (base.isEmpty() || checking) return
        checking = true
        thread {
            try {
                val remote = JSONObject(String(httpGet("$base/version.json?t=${System.currentTimeMillis()}")))
                val rv = remote.optInt("web", 0)
                if (rv > localVersion()) {
                    val tmp = File(filesDir, "www_new")
                    tmp.deleteRecursively(); tmp.mkdirs()
                    val files = remote.getJSONArray("files")
                    for (i in 0 until files.length()) {
                        val name = files.getString(i)
                        if (name.contains("..")) continue
                        val out = File(tmp, name)
                        out.parentFile?.mkdirs()
                        out.writeBytes(httpGet("$base/$name?v=$rv"))
                    }
                    File(tmp, "version.json").writeText(remote.toString())
                    val dst = File(filesDir, "www")
                    dst.deleteRecursively()
                    tmp.renameTo(dst)
                    runOnUiThread { web.evaluateJavascript("window.onHotdogUpdate && window.onHotdogUpdate()", null) }
                }
                val apk = remote.optInt("apk", 0)
                val apkUrl = remote.optString("apkUrl", "")
                if (apk > BuildConfig.VERSION_CODE && apkUrl.isNotEmpty()) {
                    runOnUiThread {
                        AlertDialog.Builder(this)
                            .setTitle("Nowa wersja My hotdog")
                            .setMessage("Jest nowa wersja aplikacji. Pobierz ją i zainstaluj na tę obecną – postęp w grze zostanie.")
                            .setPositiveButton("Pobierz") { _, _ -> startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(apkUrl))) }
                            .setNegativeButton("Później", null)
                            .show()
                    }
                }
            } catch (e: Exception) {
                // brak internetu – gramy na tym, co jest
            } finally {
                checking = false
            }
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        web.evaluateJavascript("window.hotdogBack ? window.hotdogBack() : false") { r ->
            if (r != "true") super@MainActivity.onBackPressed()
        }
    }

    override fun onPause() {
        web.evaluateJavascript("window.hotdogSave && window.hotdogSave()", null)
        super.onPause()
    }

    override fun onResume() {
        super.onResume()
        checkUpdates()
    }
}
