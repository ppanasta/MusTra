package org.mustra.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.webkit.WebViewAssetLoader;

import java.io.IOException;
import java.io.InputStream;

/**
 * MusTra for Android: shows the MusTra web app (bundled in assets/www, with
 * its Python runtime) in a WebView, so it works fully offline.
 */
public class MainActivity extends Activity {
    private static final String HOST = "appassets.androidplatform.net";
    private WebView webView;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        WebViewAssetLoader loader = new WebViewAssetLoader.Builder()
                .setDomain(HOST)
                .addPathHandler("/", new AppAssets())
                .build();

        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return loader.shouldInterceptRequest(request.getUrl());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri url = request.getUrl();
                if (HOST.equals(url.getHost())) {
                    return false;
                }
                // References and song sources open in the browser.
                startActivity(new Intent(Intent.ACTION_VIEW, url));
                return true;
            }
        });
        webView.addJavascriptInterface(new Bridge(), "MusTraAndroid");
        setContentView(webView);

        if (savedInstanceState != null) {
            webView.restoreState(savedInstanceState);
        } else {
            webView.loadUrl("https://" + HOST + "/index.html");
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        webView.saveState(outState);
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        // Let the web app close a dialog or go back to the welcome page first.
        webView.evaluateJavascript("(window.mustraBack ? window.mustraBack() : false)", handled -> {
            if (!"true".equals(handled)) {
                finish();
            }
        });
    }

    /** Serves assets/www with correct content types (WebAssembly needs one). */
    private class AppAssets implements WebViewAssetLoader.PathHandler {
        @Override
        public WebResourceResponse handle(String path) {
            if (path.isEmpty() || path.endsWith("/")) {
                path = path + "index.html";
            }
            try {
                InputStream stream = getAssets().open("www/" + path);
                String mime = mimeType(path);
                String encoding = mime.startsWith("text/") || mime.endsWith("javascript")
                        || mime.endsWith("json") ? "utf-8" : null;
                return new WebResourceResponse(mime, encoding, stream);
            } catch (IOException e) {
                return null;
            }
        }
    }

    static String mimeType(String path) {
        String p = path.toLowerCase();
        if (p.endsWith(".html")) return "text/html";
        if (p.endsWith(".js") || p.endsWith(".mjs")) return "text/javascript";
        if (p.endsWith(".css")) return "text/css";
        if (p.endsWith(".json")) return "application/json";
        if (p.endsWith(".webmanifest")) return "application/manifest+json";
        if (p.endsWith(".wasm")) return "application/wasm";
        if (p.endsWith(".zip")) return "application/zip";
        if (p.endsWith(".png")) return "image/png";
        if (p.endsWith(".svg")) return "image/svg+xml";
        return "application/octet-stream";
    }

    /** Called from app.js as window.MusTraAndroid. */
    private class Bridge {
        @JavascriptInterface
        public void exit() {
            runOnUiThread(MainActivity.this::finishAndRemoveTask);
        }

        @JavascriptInterface
        public void share(String name, String text) {
            Intent send = new Intent(Intent.ACTION_SEND);
            send.setType("application/json");
            send.putExtra(Intent.EXTRA_SUBJECT, name);
            send.putExtra(Intent.EXTRA_TEXT, text);
            runOnUiThread(() -> startActivity(Intent.createChooser(send, "Export MusTra contributions")));
        }
    }
}
