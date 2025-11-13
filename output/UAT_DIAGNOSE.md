## DIAGNOSTICS 2025-11-13T17:27:50.8410051-05:00

### UVICORN_STDERR tail
python : INFO:     Will watch for changes in these directories: 
['C:\\Users\\natha\\dev\\repos\\jcw-estimator-pro']
At C:\Users\natha\dev\repos\jcw-estimator-pro\scripts\uat_start_api
.ps1:10 char:1
+ python -m uvicorn web.backend.app_comprehensive:app --host 
$ListenHos ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~
    + CategoryInfo          : NotSpecified: (INFO:     Will ...est 
   imator-pro']:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C 
to quit)
INFO:     Started reloader process [37836] using WatchFiles
C:\Users\natha\dev\repos\jcw-estimator-pro\.venv\Lib\site-packages\
pydantic\_internal\_fields.py:149: UserWarning: Field 
"model_version" has conflict with protected namespace "model_".

You may be able to resolve this warning by setting 
`model_config['protected_namespaces'] = ()`.
  warnings.warn(
INFO:     Started server process [12668]
INFO:     Waiting for application startup.
INFO:     Application startup complete.

### uat-report.json tail
                      "retry": 0,
                      "startTime": "2025-11-13T21:50:24.224Z",
                      "annotations": [],
                      "attachments": [
                        {
                          "name": "screenshot",
                          "contentType": "image/png",
                          "path": "C:\\Users\\natha\\dev\\repos\\jcw-estimator-pro\\output\\playwright-artifacts\\uat.story.video-R2-2-2-Sto-73be8-timate-→-Interactive-video--chromium\\test-failed-1.png"
                        },
                        {
                          "name": "video",
                          "contentType": "video/webm",
                          "path": "C:\\Users\\natha\\dev\\repos\\jcw-estimator-pro\\output\\playwright-artifacts\\uat.story.video-R2-2-2-Sto-73be8-timate-→-Interactive-video--chromium\\video.webm"
                        },
                        {
                          "name": "error-context",
                          "contentType": "text/markdown",
                          "path": "C:\\Users\\natha\\dev\\repos\\jcw-estimator-pro\\output\\playwright-artifacts\\uat.story.video-R2-2-2-Sto-73be8-timate-→-Interactive-video--chromium\\error-context.md"
                        }
                      ],
                      "errorLocation": {
                        "file": "C:\\Users\\natha\\dev\\repos\\jcw-estimator-pro\\tests\\e2e\\uat.story.video.spec.ts",
                        "column": 75,
                        "line": 13
                      }
                    }
                  ],
                  "status": "unexpected"
                }
              ],
              "id": "3a59ad2d85df6388cd42-75e944c36667f0fc9196",
              "file": "uat.story.video.spec.ts",
              "line": 7,
              "column": 7
            }
          ]
        }
      ]
    }
  ],
  "errors": [],
  "stats": {
    "startTime": "2025-11-13T21:50:23.389Z",
    "duration": 12850.347000000002,
    "expected": 14,
    "skipped": 1,
    "unexpected": 6,
    "flaky": 0
  }
}
