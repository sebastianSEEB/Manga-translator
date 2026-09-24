# iPhone: Shortcut + private Tailscale connection

This is the simplest phase-2 route. It displays a translated screenshot in Quick
Look; it does not inject an overlay into Safari. There is no Xcode requirement.
The backend's `/translate/image` endpoint is implemented. The Shortcut must be
assembled on your phone; no Apple-signed `.shortcut` file is included.

## A. Connect your desktop and iPhone

1. Install Tailscale on both devices and sign in to the same tailnet.
2. Keep the backend running on desktop at `127.0.0.1:8000` using the README command.
3. In your desktop terminal, run:

```bash
tailscale serve --bg http://127.0.0.1:8000
```

4. Follow any Tailscale prompt to enable HTTPS. Record the HTTPS URL it prints,
   for example `https://your-computer.your-tailnet.ts.net`.
5. Add that exact hostname (without `https://`, port or path) to `.env`:

```dotenv
EXTRA_ALLOWED_HOSTS=your-computer.your-tailnet.ts.net
```

6. Restart the backend. In iPhone Safari, with Tailscale connected, open the
   printed URL plus `/health`. It should show JSON with `status: ready`.

Use **Serve**, which is private to the tailnet. Do not enable Tailscale Funnel
or router port forwarding. Keep the backend token: tailnet membership does not
replace endpoint authentication. Existing Serve configurations may use ports
already; inspect `tailscale serve status` before changing them. To undo this
setup later, use `tailscale serve reset` only if no other services rely on it.
Tailscale ACLs must permit your phone to reach this desktop.

## B. Build “Translate manga” in Shortcuts

Create a new Shortcut and add these actions in order. Action labels may vary
slightly by iOS language/version.

1. **Take Screenshot**.
2. **Convert Image**: input = Screenshot; format = **PNG**.
3. **URL**: `https://YOUR-TAILSCALE-HOST/translate/image?series=wangan-midnight`
4. **Get Contents of URL**:
   - URL = the URL above.
   - Expand options; Method = **POST**.
   - Add header `Authorization` with value `Bearer YOUR_BACKEND_TOKEN`.
   - Add header `Content-Type` with value `image/png`.
   - Request Body = **File**.
   - File = the **Converted Image** magic variable from step 2.
   - Do not choose JSON or form data: the endpoint expects raw PNG bytes.
5. **Quick Look**: input = Contents of URL.

Do not add Save to Photos or Save File actions if you want transient viewing.
Quick Look receives an image response; a JSON response indicates an error, such
as invalid token (401), a busy backend (429), or model failure (502).

Run the Shortcut while the manga is visible in Safari. A convenient launcher is
**Settings → Accessibility → Touch → Back Tap → Double Tap → Translate manga**.
This avoids taking a screenshot of the Shortcuts editor. If Back Tap isn't
available, use an appropriate device shortcut/Action Button or Siri launcher.
Check that it captures Safari rather than the launcher UI on your device.

Alternative: make it a share-sheet Shortcut receiving Images, replace **Take
Screenshot** with **Shortcut Input**, and share an existing screenshot into it.
That input screenshot may already be saved by iOS; the backend does not delete it.

## C. How the result looks

The backend covers each detected text region with white, wraps English text,
and returns PNG bytes without saving a file. Tiny regions that cannot fit at a
readable size receive a number; the full corresponding English is appended
below the image. This avoids silently truncating translations. Background art
under text is not reconstructed; LaMa inpainting remains optional v2.

The iPhone route uses the same series glossary and session cache as Chrome.
Change `series=` in the URL for another series created in desktop settings.
The desktop must remain awake and connected. Slow local OCR/LLM work may exceed
iOS's request timeout; reduce screenshot dimensions or use a faster model.
No universal five-second or Shortcut-timeout guarantee has been established.

The token is stored in the Shortcut configuration. Do not publish or share the
Shortcut with the token inside it. Shortcuts/iCloud sync and OS temporary image
handling have their own behavior outside the backend's memory-only policy.

## References

- Apple, API requests and request bodies in Shortcuts:
  https://support.apple.com/guide/shortcuts/request-your-first-api-apd58d46713f/ios
- Tailscale Serve:
  https://tailscale.com/docs/features/tailscale-serve
