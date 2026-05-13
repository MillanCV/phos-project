import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Camera, Download, X } from "lucide-react";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/Card";
import { Toast } from "../../components/ui/Toast";
import { cn } from "../../lib/cn";
import { apiClient } from "../../shared/api-client";
import { CameraControlsCard } from "../camera-controls/CameraControlsCard";

type CaptureRecord = {
  id: string;
  file_path: string;
  captured_at: string;
  source: string;
  preview_url: string;
  download_url: string;
};

const API_PREFIX = "/api";

function resolveCaptureAssetUrl(rawUrl: string): string {
  if (rawUrl.startsWith("http")) return rawUrl;
  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? API_PREFIX).replace(
    /\/$/,
    "",
  );
  const normalizedPath = rawUrl.startsWith("/") ? rawUrl : `/${rawUrl}`;

  if (
    apiBaseUrl.endsWith(API_PREFIX) &&
    normalizedPath.startsWith(`${API_PREFIX}/`)
  ) {
    return `${apiBaseUrl}${normalizedPath.slice(API_PREFIX.length)}`;
  }
  return `${apiBaseUrl}${normalizedPath}`;
}

/** Browser <img> hits this URL directly (not apiClient); must match FastAPI `/api/camera/liveview/stream`. */
function getLiveViewStreamUrl(session: number): string {
  const base = (import.meta.env.VITE_API_BASE_URL ?? "/api").replace(/\/$/, "");
  if (base === "/api" || base.endsWith("/api")) {
    const prefix = base === "/api" ? "/api" : base;
    return `${prefix}/camera/liveview/stream?session=${session}`;
  }
  return `${base}/api/camera/liveview/stream?session=${session}`;
}

type ViewTab = "picture" | "live";

export function ManualCaptureCard() {
  const [latest, setLatest] = useState<CaptureRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [imageNonce, setImageNonce] = useState(0);
  const [viewTab, setViewTab] = useState<ViewTab>("picture");
  const [liveViewSession, setLiveViewSession] = useState(0);
  const [liveViewError, setLiveViewError] = useState("");
  const liveViewImgRef = useRef<HTMLImageElement | null>(null);

  const imageUrl = useMemo(() => {
    if (!latest) return null;
    const base = resolveCaptureAssetUrl(latest.preview_url);
    return `${base}?ts=${encodeURIComponent(latest.captured_at)}&n=${imageNonce}`;
  }, [latest, imageNonce]);
  const downloadUrl = useMemo(() => {
    if (!latest) return null;
    return resolveCaptureAssetUrl(latest.download_url);
  }, [latest]);
  const liveViewUrl = useMemo(() => {
    if (viewTab !== "live") return null;
    return getLiveViewStreamUrl(liveViewSession);
  }, [viewTab, liveViewSession]);
  const [isPreviewOpen, setPreviewOpen] = useState(false);

  const bumpLiveSession = useCallback(() => {
    setLiveViewError("");
    setLiveViewSession((s) => s + 1);
  }, []);

  const loadLatest = useCallback(async () => {
    setError("");
    setViewTab("picture");
    bumpLiveSession();
    try {
      const result = await apiClient.get<CaptureRecord | null>(
        "/capture/latest",
      );
      setLatest(result);
      setImageNonce((value) => value + 1);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load latest capture",
      );
    }
  }, [bumpLiveSession]);

  useEffect(() => {
    const id = window.setTimeout(() => {
      void loadLatest();
    }, 0);
    return () => window.clearTimeout(id);
  }, [loadLatest]);

  const selectPictureTab = () => {
    setViewTab("picture");
    bumpLiveSession();
  };

  const selectLiveTab = () => {
    setLiveViewError("");
    setViewTab("live");
    bumpLiveSession();
  };

  useLayoutEffect(() => {
    if (viewTab === "live") return;
    liveViewImgRef.current?.removeAttribute("src");
    liveViewImgRef.current?.removeAttribute("srcset");
  }, [viewTab]);

  const capture = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await apiClient.post<CaptureRecord>("/capture/photo");
      bumpLiveSession();
      setViewTab("picture");
      setLatest(result);
      setImageNonce((value) => value + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not take photo");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="md:col-span-2 grid gap-4 lg:grid-cols-2 lg:items-start">
      <Card className="min-h-0">
        <CardHeader>
          <div className="space-y-1">
            <CardTitle>View &amp; capture</CardTitle>
            <CardDescription>
              Latest photo or live preview (MJPEG). Leaving live view stops the
              stream.
            </CardDescription>
          </div>
          <div
            className="mt-3 flex rounded-md border border-border bg-muted/30 p-0.5 text-sm"
            role="tablist"
            aria-label="View mode"
          >
            <button
              type="button"
              role="tab"
              aria-selected={viewTab === "picture"}
              className={cn(
                "flex-1 rounded px-3 py-2 font-medium transition-colors",
                viewTab === "picture"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-mutedForeground hover:text-foreground",
              )}
              onClick={selectPictureTab}
            >
              Latest photo
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={viewTab === "live"}
              className={cn(
                "flex-1 rounded px-3 py-2 font-medium transition-colors",
                viewTab === "live"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-mutedForeground hover:text-foreground",
              )}
              onClick={selectLiveTab}
            >
              Live view
            </button>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="min-h-[12rem] flex-1">
            {viewTab === "picture" &&
              (imageUrl ? (
                <div className="overflow-hidden rounded-md border border-border/60 bg-black/40">
                  <img
                    src={imageUrl}
                    alt="Latest capture"
                    className="max-h-[min(28rem,70vh)] w-full object-contain"
                    loading="lazy"
                  />
                </div>
              ) : (
                <p className="rounded-md border border-dashed border-border/60 bg-muted/20 px-4 py-12 text-center text-sm text-mutedForeground">
                  No capture yet. Take a photo or load the latest below.
                </p>
              ))}
            {viewTab === "live" && liveViewUrl && (
              <div className="overflow-hidden rounded-md border border-border/60 bg-black">
                <img
                  key={liveViewSession}
                  ref={liveViewImgRef}
                  src={liveViewUrl}
                  alt="Camera live view"
                  className="max-h-[min(28rem,70vh)] w-full object-contain"
                  loading="eager"
                  onError={() => {
                    setLiveViewError("Live view interrupted. Retrying…");
                    if (viewTab === "live") {
                      setTimeout(() => {
                        setLiveViewSession((session) => session + 1);
                      }, 800);
                    }
                  }}
                />
              </div>
            )}
            {viewTab === "live" && liveViewError && (
              <Toast variant="danger">{liveViewError}</Toast>
            )}
          </div>

          <div className="border-t border-border/60 pt-4 space-y-3">
            <div className="flex flex-wrap gap-2">
              <Button disabled={loading} onClick={() => void capture()}>
                <Camera className="h-4 w-4" />
                {loading ? "Shooting…" : "Take photo"}
              </Button>
              <Button variant="secondary" onClick={() => void loadLatest()}>
                <Download className="h-4 w-4" />
                Load latest
              </Button>
              <Button
                variant="ghost"
                disabled={!imageUrl}
                onClick={() => setPreviewOpen(true)}
              >
                Full size
              </Button>
              {downloadUrl ? (
                <a
                  href={downloadUrl}
                  className="inline-flex items-center justify-center gap-2 rounded-md border border-border bg-transparent px-3 py-2 text-sm font-medium text-mutedForeground transition-all duration-150 hover:bg-muted/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-background focus-visible:ring-primary/40"
                  target="_blank"
                  rel="noopener noreferrer"
                  download
                >
                  Download
                </a>
              ) : (
                <Button variant="ghost" disabled>
                  Download
                </Button>
              )}
            </div>
            {loading && (
              <p className="text-xs text-mutedForeground">
                Capturing — this can take a few seconds.
              </p>
            )}
            {error && <Toast variant="danger">{error}</Toast>}
            {latest ? (
              <div className="grid gap-1.5 text-xs text-mutedForeground sm:grid-cols-3 sm:gap-x-3">
                <div className="min-w-0 sm:col-span-3">
                  <span className="text-foreground">File </span>
                  <span className="break-all">{latest.file_path}</span>
                </div>
                <div>
                  <span className="text-foreground">Time </span>
                  {new Date(latest.captured_at).toLocaleString()}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-foreground">Source</span>
                  <Badge variant="default">{latest.source}</Badge>
                </div>
              </div>
            ) : (
              <p className="text-xs text-mutedForeground">No captures on record.</p>
            )}
          </div>
        </CardContent>
      </Card>

      <CameraControlsCard compact />

      {isPreviewOpen && imageUrl && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6"
          role="button"
          tabIndex={0}
          onClick={() => setPreviewOpen(false)}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              setPreviewOpen(false);
            }
          }}
        >
          <div
            className="relative max-h-full max-w-full"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              className="absolute right-2 top-2 inline-flex items-center justify-center rounded-md border border-border bg-black/70 p-1 text-white hover:bg-black/90"
              onClick={() => setPreviewOpen(false)}
              aria-label="Close full size"
            >
              <X className="h-4 w-4" />
            </button>
            <img
              src={imageUrl}
              alt="Capture full size"
              className="max-h-full max-w-full rounded-md border border-border/60 bg-black object-contain"
            />
          </div>
        </div>
      )}
    </div>
  );
}
