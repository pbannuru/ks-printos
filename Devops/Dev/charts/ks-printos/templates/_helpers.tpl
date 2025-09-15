{{/*
Expand the name of the chart.
*/}}
{{- define "ks-printos.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "ks-printos.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ks-printos.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ks-printos.labels" -}}
helm.sh/chart: {{ include "ks-printos.chart" . }}
{{ include "ks-printos.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ks-printos.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ks-printos.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app: {{ .Chart.Name }}
version: {{ .Values.deployment.version }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "ks-printos.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ks-printos.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{- define "ks-printos.namespace" -}}
{{- default "default" .Values.namespace }}
{{- end}}

{{- define "ks-printos.virtualhosts"}}
{{- if .Values.namespace }}
{{- printf "%s.%s.svc.cluster.local" .Release.Name .Values.namespace }}
{{- else }}
{{- include "ks-printos.name" . }}
{{- end }}
{{- end }}

{{- define "ks-printos.common_secret"}}
{{- printf "common-%s-secret" (include "ks-printos.name" .) }}
{{- end }}

{{- define "ks-printos.rds_secret"}}
{{- printf "rds-%s-secret" (include "ks-printos.name" .) }}
{{- end }}

{{- define "ks-printos.common_secret_provider"}}
{{- printf "common-%s-secret" (include "ks-printos.name" .) }}
{{- end }}

{{- define "ks-printos.rds_secret_provider"}}
{{- printf "rds-%s-secret" (include "ks-printos.name" .) }}
{{- end }}

{{- define "ks-printos.rds_volume_secrets"}}
{{- printf "rds-%s-vol" (include "ks-printos.name" .) }}
{{- end }}

{{- define "ks-printos.common_volume_secrets"}}
{{- printf "common-%s-vol" (include "ks-printos.name" .) }}
{{- end }}


{{- define "uuidv4" }}
{{- `{{- uuidv4 -}}` }}
{{- end }}


