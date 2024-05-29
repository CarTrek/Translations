using System;
using System.IO;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

class Program
{
    static void Main(string[] args)
    {
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(CamelCaseNamingConvention.Instance)
            .Build();

        var yamlFiles = Directory.GetFiles(".", "*.yaml", SearchOption.AllDirectories);

        foreach (var yamlFile in yamlFiles)
        {
            try
            {
                var yamlContent = File.ReadAllText(yamlFile);
                var yamlObject = deserializer.Deserialize<object>(yamlContent);
                Console.WriteLine($"{yamlFile}: OK");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"{yamlFile}: INVALID - {ex.Message}");
                Environment.Exit(1);
            }
        }
    }
}
