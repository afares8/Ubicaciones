using System;
using System.Web.Http;
using Owin;
using Microsoft.Owin.Hosting;

namespace WmsSapDiService
{
    public class Startup
    {
        public void Configuration(IAppBuilder appBuilder)
        {
            HttpConfiguration config = new HttpConfiguration();
            config.Routes.MapHttpRoute(
                name: "DefaultApi",
                routeTemplate: "{controller}/{action}",
                defaults: new { id = RouteParameter.Optional }
            );
            appBuilder.UseWebApi(config);
        }
    }

    public class HealthController : ApiController
    {
        [HttpGet]
        public IHttpActionResult Index()
        {
            try
            {
                string server = Environment.GetEnvironmentVariable("SAP_DI_SERVER");
                string companyDB = Environment.GetEnvironmentVariable("SAP_COMPANY_DB");
                string username = Environment.GetEnvironmentVariable("SAP_USERNAME");
                string password = Environment.GetEnvironmentVariable("SAP_PASSWORD");

                if (string.IsNullOrEmpty(server) || string.IsNullOrEmpty(companyDB) || 
                    string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
                {
                    return Ok(new { ok = false, message = "SAP connection parameters not configured", connected = false });
                }

                var connectionManager = SAPConnectionManager.GetInstance(server, companyDB, username, password, SAPbobsCOM.BoDataServerTypes.dst_MSSQL2016);
                var company = connectionManager.GetConnection(out string errorMsg);
                
                if (company != null && company.Connected)
                {
                    return Ok(new { ok = true, connected = true, company = companyDB });
                }
                else
                {
                    return Ok(new { ok = false, message = errorMsg ?? "Connection failed", connected = false });
                }
            }
            catch (Exception ex)
            {
                return Ok(new { ok = false, message = ex.Message, connected = false });
            }
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            string host = Environment.GetEnvironmentVariable("SAP_DI_HOST") ?? "localhost";
            string port = Environment.GetEnvironmentVariable("SAP_DI_PORT") ?? "8001";
            string baseAddress = $"http://{host}:{port}/";

            string server = Environment.GetEnvironmentVariable("SAP_DI_SERVER");
            string companyDB = Environment.GetEnvironmentVariable("SAP_COMPANY_DB");
            string username = Environment.GetEnvironmentVariable("SAP_USERNAME");
            string password = Environment.GetEnvironmentVariable("SAP_PASSWORD");

            if (!string.IsNullOrEmpty(server) && !string.IsNullOrEmpty(companyDB) && 
                !string.IsNullOrEmpty(username) && !string.IsNullOrEmpty(password))
            {
                var connectionManager = SAPConnectionManager.GetInstance(server, companyDB, username, password, SAPbobsCOM.BoDataServerTypes.dst_MSSQL2016);
                Console.WriteLine("SAP Connection Manager initialized for WMS");
            }
            else
            {
                Console.WriteLine("WARNING: SAP connection parameters not configured - connection manager will initialize on first request");
            }

            using (WebApp.Start<Startup>(url: baseAddress))
            {
                Console.WriteLine("WMS SAP DI API Service running at " + baseAddress);
                Console.WriteLine("Press any key to exit...");
                Console.ReadKey();
                
                Console.WriteLine("Shutting down SAP connection...");
                SAPConnectionManager.DisposeInstance();
            }
        }
    }
}
