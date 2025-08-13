using System;
using System.Threading;
using SAPbobsCOM;

namespace WmsSapDiService
{
    public class SAPConnectionManager
    {
        private static SAPConnectionManager _instance;
        private static readonly object _lock = new object();
        private Company _company;
        private readonly string _server;
        private readonly string _companyDB;
        private readonly string _username;
        private readonly string _password;
        private readonly BoDataServerTypes _serverType;

        private SAPConnectionManager(string server, string companyDB, string username, string password, BoDataServerTypes serverType)
        {
            _server = server;
            _companyDB = companyDB;
            _username = username;
            _password = password;
            _serverType = serverType;
        }

        public static SAPConnectionManager GetInstance(string server, string companyDB, string username, string password, BoDataServerTypes serverType)
        {
            if (_instance == null)
            {
                lock (_lock)
                {
                    if (_instance == null)
                    {
                        _instance = new SAPConnectionManager(server, companyDB, username, password, serverType);
                    }
                }
            }
            return _instance;
        }

        public Company GetConnection(out string errorMessage)
        {
            lock (_lock)
            {
                errorMessage = null;

                if (_company != null && _company.Connected)
                {
                    return _company;
                }

                try
                {
                    if (_company != null)
                    {
                        _company.Disconnect();
                        System.Runtime.InteropServices.Marshal.ReleaseComObject(_company);
                    }

                    _company = new Company();
                    _company.Server = _server;
                    _company.CompanyDB = _companyDB;
                    _company.UserName = _username;
                    _company.Password = _password;
                    _company.DbServerType = _serverType;
                    _company.language = BoSuppLangs.ln_English;

                    int result = _company.Connect();
                    if (result != 0)
                    {
                        _company.GetLastError(out int errCode, out string errMsg);
                        errorMessage = $"Connection failed: {errCode} - {errMsg}";
                        return null;
                    }

                    Console.WriteLine($"✅ Connected to SAP Business One - Company: {_companyDB}");
                    return _company;
                }
                catch (Exception ex)
                {
                    errorMessage = $"Exception during connection: {ex.Message}";
                    return null;
                }
            }
        }

        public void Disconnect()
        {
            lock (_lock)
            {
                try
                {
                    if (_company != null && _company.Connected)
                    {
                        _company.Disconnect();
                        Console.WriteLine("SAP connection disconnected");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error disconnecting: {ex.Message}");
                }
                finally
                {
                    if (_company != null)
                    {
                        System.Runtime.InteropServices.Marshal.ReleaseComObject(_company);
                        _company = null;
                    }
                }
            }
        }

        public static void DisposeInstance()
        {
            if (_instance != null)
            {
                _instance.Disconnect();
                _instance = null;
            }
        }
    }
}
