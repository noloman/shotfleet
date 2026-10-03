package com.shotfleet.fixture;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

// A tiny two-screen app with strings in five languages: shotfleet's Android end-to-end test fixture
// (tools/fixture-app-android/build.sh). Same screens and words as tools/fixture-app (the iOS one).
public class MainActivity extends Activity {
    private boolean onSettings;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        render();
    }

    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }

    private void render() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(Color.WHITE);
        root.setPadding(dp(32), dp(32), dp(32), dp(32));

        View badge = new View(this);
        GradientDrawable circle = new GradientDrawable();
        circle.setShape(GradientDrawable.OVAL);
        circle.setColor(onSettings ? Color.rgb(52, 120, 246) : Color.rgb(0, 150, 136));
        root.addView(badge, new LinearLayout.LayoutParams(dp(96), dp(96)));
        badge.setBackground(circle);

        TextView title = new TextView(this);
        title.setText(onSettings ? R.string.settings : R.string.welcome);
        title.setTextSize(34);
        title.setTypeface(null, android.graphics.Typeface.BOLD);
        title.setTextColor(Color.BLACK);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(28), 0, dp(12));
        root.addView(title);

        TextView body = new TextView(this);
        body.setText(onSettings ? R.string.settings_hint : R.string.tagline);
        body.setTextSize(20);
        body.setTextColor(Color.DKGRAY);
        body.setGravity(Gravity.CENTER);
        body.setPadding(0, 0, 0, dp(28));
        root.addView(body);

        Button button = new Button(this);
        button.setText(onSettings ? R.string.done : R.string.next);
        button.setAllCaps(false);  // the screenshot shows the string as translated
        button.setTextSize(20);
        button.setOnClickListener(v -> { onSettings = !onSettings; render(); });
        root.addView(button);

        setContentView(root);
    }
}
