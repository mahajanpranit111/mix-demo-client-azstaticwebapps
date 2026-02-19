FROM ubuntu:20.04

ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1		    \
    PYTHONDONTWRITEBYTECODE=1                       \
    HOME=/home/site/wwwroot                         \
    FUNCTIONS_CORE_TOOLS_TELEMETRY_OPTOUT=1         \
    DOTNET_CLI_TELEMETRY_OPTOUT=1

WORKDIR $HOME

RUN apt-get update -y                               \
&& apt-get install -y wget python3 python3-pip      \   
&& cp /usr/bin/python3 /usr/bin/python              \
&& wget -q https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb \
&& dpkg -i packages-microsoft-prod.deb              \ 
&& apt-get update -y                                \
&& apt-get install -y azure-functions-core-tools-4  

# Pre-create telemetry consent sentinel so func doesn't prompt interactively
RUN mkdir -p /root/.azure-functions-core-tools \
    && echo "true" > /root/.azure-functions-core-tools/telemetryDefaultRecorded \
    && mkdir -p $HOME/.azure-functions-core-tools \
    && echo "true" > $HOME/.azure-functions-core-tools/telemetryDefaultRecorded

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . ./api

WORKDIR $HOME/api

CMD ["func", "host", "start", "--cors", "*"]
