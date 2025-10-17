import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { BarcodeDetector, prepareZXingModule } from 'barcode-detector/ponyfill';

import { useLanguage } from '@/contexts/LanguageContext';
import { Loader, Scan, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

// Override the locateFile function
prepareZXingModule({
  overrides: {
    locateFile: (path, prefix) => {
      if (path.endsWith('.wasm')) {
        return `/lib/wasm/${path}`;
      }
      return prefix + path;
    },
  },
});
interface BarcodeScannerProps {
  onScan: (barcode: string) => void;
  title?: string; // optional override for dialog title
}

export const BarcodeScanner: React.FC<BarcodeScannerProps> = ({ onScan, title }) => {
  const { t } = useLanguage();
  // Determine whether the implementation is the browser's native BarcodeDetector
  const isNativeBarcodeDetector = (() => {
    try {
      const bd = (globalThis as any).BarcodeDetector;
      if (!bd) return false;
      const str = Function.prototype.toString.call(bd);
      return str.includes('[native code]');
    } catch (e) {
      return false;
    }
  })();
  const [isOpen, setIsOpen] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detectedBarcode, setDetectedBarcode] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const detectorRef = useRef<BarcodeDetector | null>(null);

  useEffect(() => {
    // Initialize detector when component mounts
    const initDetector = async () => {
      try {
        detectorRef.current = new BarcodeDetector({
          formats: [
            'ean_13', // ISBN-13 is encoded as EAN-13
            'ean_8',
            'upc_a',
            'upc_e',
            'code_128',
            'code_39',
            'code_93',
          ],
        });
        setIsInitialized(true);
      } catch (err) {
        setError('Failed to initialize barcode detector');
      }
    };
    initDetector();
  }, []);

  const startScanning = async () => {
    // Wait for detector to be initialized
    if (!detectorRef.current) {
      // Retry after a short delay
      await new Promise(resolve => setTimeout(resolve, 100));

      if (!detectorRef.current) {
        setError('Barcode detector failed to initialize. Please refresh the page.');
        return;
      }
    }

    if (!videoRef.current) {
      setError('Video element not available');
      return;
    }

    try {
      setError(null);

      // Request camera access
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      });

      streamRef.current = stream;
      videoRef.current.srcObject = stream;

      await videoRef.current.play();

      // This is the key change: We now set the state and let the useEffect handle the loop.
      setIsScanning(true);
    } catch (err) {
      setError('Failed to access camera. Please check permissions.');
      setIsScanning(false);
    }
  };

  // This new useEffect hook ensures the scan loop starts only after the state is updated.
  useEffect(() => {
    if (isScanning) {
      scanFrame();
    }
  }, [isScanning]);

  const scanFrame = async () => {
    if (!videoRef.current || !detectorRef.current || !isScanning) {
      return;
    }

    try {
      // New logging in the scan loop
      if (videoRef.current.readyState < 2) {
        // Wait for the video to have enough data
        await new Promise(resolve => {
          const checkReadyState = () => {
            if (videoRef.current && videoRef.current.readyState >= 2) {
              resolve(null);
            } else {
              requestAnimationFrame(checkReadyState);
            }
          };
          checkReadyState();
        });
      }

      const barcodes = await detectorRef.current.detect(videoRef.current);

      if (barcodes.length > 0) {
        setDetectedBarcode(barcodes[0].rawValue);

        // Call the callback with the detected barcode
        onScan(barcodes[0].rawValue);

        // Stop scanning after successful detection
        stopScanning();
        setIsOpen(false);

        return;
      }
    } catch (err) {
      // Silent error handling
    }

    // Continue scanning
    animationFrameRef.current = requestAnimationFrame(scanFrame);
  };

  const stopScanning = () => {
    setIsScanning(false);

    // Cancel animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    // Stop video stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    // Clear video source
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setDetectedBarcode(null);
  };

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open);

    if (!open) {
      stopScanning();
    }
  };

  useEffect(() => {
    if (isOpen) {
      // Use a timeout to allow the dialog to render and the videoRef to be set.
      const timer = setTimeout(() => {
        startScanning();
      }, 150); // A small delay is often necessary for portal-based dialogs

      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      stopScanning();
    };
  }, []);

  return (
    <>
      <Button
        type="button"
        variant="outline"
        size="icon"
        onClick={() => handleOpenChange(true)}
        title={title ?? t('scanner.open')}
        disabled={!isInitialized}
      >
        {!isInitialized ? (
          <Loader className="h-4 w-4 animate-spin" />
        ) : (
          <Scan className="h-4 w-4" />
        )}
      </Button>

      <Dialog open={isOpen} onOpenChange={handleOpenChange}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>{title ?? t('scanner.title')}</DialogTitle>
            <DialogDescription>{t('scanner.description')}</DialogDescription>
            <div className="mt-2 text-xs text-muted-foreground">
              {isNativeBarcodeDetector ? t('scanner.usingNative') : t('scanner.usingPolyfill')}
            </div>
          </DialogHeader>

          <div className="space-y-4">
            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive rounded-md">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
              <video ref={videoRef} className="w-full h-full object-cover" playsInline muted />

              {/* Scanning overlay */}
              {isScanning && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-64 h-48 border-4 border-primary rounded-lg">
                    <div className="absolute inset-x-0 top-1/2 h-0.5 bg-primary animate-pulse" />
                  </div>
                </div>
              )}

              {/* Loading indicator */}
              {!isScanning && !error && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                  <div className="text-center space-y-2">
                    <Loader className="h-8 w-8 text-white animate-spin mx-auto" />
                    <p className="text-white text-sm">{t('scanner.initializingCamera')}</p>
                  </div>
                </div>
              )}

              {/* Detected barcode display */}
              {detectedBarcode && (
                <div className="absolute bottom-4 left-4 right-4 p-3 bg-green-500/90 rounded-md">
                  <p className="text-sm text-white font-medium text-center">
                    {t('scanner.detected')}: {detectedBarcode}
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
                <X className="h-4 w-4 mr-2" />
                {t('common.cancel')}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
